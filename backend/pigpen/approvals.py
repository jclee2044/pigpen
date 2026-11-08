from uuid import uuid5, NAMESPACE_URL
from sqlalchemy import select
from . import schema as s
from .records import get, expect
from .domain import all_approved
from .errors import DomainError


class ApprovalServices:
    def do_wishlist_reorder(self,c,op):
        household=self.household(c)
        legacy=op['entity_id']!=household['id']
        target=get(c,s.users,op['entity_id']) if legacy else household
        expect(target,op['data']['expected_revision'])
        ids=op['data']['item_ids']
        wishes=[dict(row) for row in c.execute(select(s.wishlist_items).where(
            s.wishlist_items.c.deleted.is_(False))).mappings()]
        available={row['id'] for row in wishes if not legacy or row['owner_id']==target['id']}
        if len(ids)!=len(set(ids)) or not set(ids)<=available:
            raise DomainError('wishlist','Order must contain unique existing wishes in the target list')
        existing=[value for value in household['wishlist_order'] if any(row['id']==value for row in wishes)]
        existing += [row['id'] for row in sorted(wishes,key=lambda row:(row['created_at'],row['id'])) if row['id'] not in existing]
        if legacy:
            owner_order=ids+[value for value in existing if value in available and value not in ids]
            result=self.save(c,s.users,{'wishlist_order':owner_order},target)
            positions=iter(owner_order)
            order=[next(positions) if value in available else value for value in existing]
            self.save(c,s.households,{'wishlist_order':order},household)
            return result
        order=ids+[value for value in existing if value not in ids]
        return self.save(c,s.households,{'wishlist_order':order},household)

    def do_wishlist_create(self,c,op):
        result=self.save(c,s.wishlist_items,dict(id=op['entity_id'],owner_id=op['actor_id'],**op['data'],status='active'))
        self.notify(c,op,'wishlist.created','wishlist-items',result['id'])
        return result

    def do_wishlist_update(self,c,op):
        row=get(c,s.wishlist_items,op['entity_id']);data=dict(op['data']);expect(row,data.pop('expected_revision'))
        if row['owner_id']!=op['actor_id']:
            raise DomainError('actor','Only the owner manages their wish list',403)
        return self.save(c,s.wishlist_items,data,row)

    def do_wishlist_delete(self,c,op):
        row=get(c,s.wishlist_items,op['entity_id']);expect(row,op['data']['expected_revision'])
        if row['owner_id']!=op['actor_id']:
            raise DomainError('actor','Only the owner manages their wish list',403)
        return self.save(c,s.wishlist_items,{'deleted':True},row)

    def request_category(self,c,category_id):
        if category_id:
            self.bill_category(c,category_id)

    def do_request_create(self,c,op):
        self.request_category(c,op['data']['category_id'])
        result=self.save(c,s.approval_requests,dict(id=op['entity_id'],requester_id=op['actor_id'],**op['data'],status='open',purchase_id=None,approved_revision=None))
        self.notify(c,op,'request.created','approval-requests',result['id'])
        return result

    def editable_request(self,c,op):
        row=get(c,s.approval_requests,op['entity_id']);expect(row,op['data']['expected_revision'])
        if row['requester_id']!=op['actor_id']:
            raise DomainError('actor','Only the requester can revise or cancel a request',403)
        if row['status']!='open':
            raise DomainError('request_closed','Request is no longer open',409,row)
        return row

    def do_request_update(self,c,op):
        row=self.editable_request(c,op);data=dict(op['data']);data.pop('expected_revision')
        self.request_category(c,data['category_id'])
        if all(row[k]==v for k,v in data.items()):
            return row
        result=self.save(c,s.approval_requests,data,row)
        for vote in c.execute(select(s.approval_votes).where(s.approval_votes.c.request_id==row['id'])).mappings():
            if vote['approved']:
                self.save(c,s.approval_votes,{'approved':False},dict(vote))
        self.notify(c,op,'request.revised','approval-requests',row['id'])
        return result

    def do_request_cancel(self,c,op):
        row=self.editable_request(c,op)
        result=self.save(c,s.approval_requests,{'status':'canceled'},row)
        self.notify(c,op,'request.canceled','approval-requests',row['id'])
        return result

    def do_request_delete(self,c,op):
        row=get(c,s.approval_requests,op['entity_id']);expect(row,op['data']['expected_revision'])
        if row['requester_id']!=op['actor_id']:
            raise DomainError('actor','Only the requester can delete a request',403)
        if row['status']=='purchased':
            raise DomainError('request_closed','Purchased requests must retain their purchase history',409,row)
        return self.save(c,s.approval_requests,{'deleted':True},row)

    def do_request_deny(self,c,op):
        row=get(c,s.approval_requests,op['entity_id']);expect(row,op['data']['expected_revision'])
        if row['requester_id']==op['actor_id']:
            raise DomainError('actor','Requester cannot deny their own request',403)
        if row['status']!='open':
            raise DomainError('request_closed','Request is no longer open',409,row)
        result=self.save(c,s.approval_requests,{'status':'denied'},row)
        self.save(c,s.comments,dict(id=str(uuid5(NAMESPACE_URL,op['operation_id']+'/denial')),
            actor_id=op['actor_id'],target_resource='approval-requests',target_id=row['id'],
            text='Request denied: '+op['data']['reason']))
        self.notify(c,op,'request.denied','approval-requests',row['id'])
        return result

    def request_detail(self,c,request_id):
        row=get(c,s.approval_requests,request_id)
        votes=[dict(v) for v in c.execute(select(s.approval_votes).where(s.approval_votes.c.request_id==row['id'])).mappings()]
        active=list(c.execute(select(s.users.c.id).where(s.users.c.active==True,s.users.c.deleted==False)).scalars())
        eligible=[x for x in active if x!=row['requester_id']]
        return {**row,'votes':votes,'eligible_reviewer_ids':eligible,
                'approved':row['status']=='purchased' or (row['status']=='open' and row['requester_id'] in active and all_approved(row['requester_id'],active,votes,row['revision']))}

    def do_vote_set(self,c,op):
        data=op['data'];request=get(c,s.approval_requests,data['request_id'])
        get(c,s.users,request['requester_id'],active=True)
        if request['requester_id']==op['actor_id']:
            raise DomainError('self_approval','Requester cannot approve their own request',403)
        if request['status']!='open':
            raise DomainError('request_closed','Request is no longer open',409,request)
        expect(request,data['request_revision'])
        existing=c.execute(select(s.approval_votes).where(s.approval_votes.c.request_id==request['id'],s.approval_votes.c.reviewer_id==op['actor_id'])).mappings().first()
        existing=dict(existing) if existing else None
        if existing:
            if existing['id']!=op['entity_id']:
                raise DomainError('vote_id','Use the existing reviewer vote ID',409,existing)
            expect(existing,data['expected_revision'])
            if existing['approved']==data['approved'] and existing['request_revision']==data['request_revision']:
                return existing
        elif data['expected_revision']:
            raise DomainError('revision_conflict','New votes require revision 0',409)
        vote=self.save(c,s.approval_votes,dict(id=op['entity_id'],request_id=request['id'],reviewer_id=op['actor_id'],
            approved=data['approved'],request_revision=data['request_revision']),existing)
        self.notify(c,op,'approval.on' if data['approved'] else 'approval.off','approval-requests',request['id'])
        return vote

    def link_request(self,c,request_id,revision,op):
        request=get(c,s.approval_requests,request_id)
        if request['status']!='open':
            raise DomainError('request_closed','Request already purchased or canceled',409,request)
        expect(request,revision)
        detail=self.request_detail(c,request_id)
        if not detail['approved']:
            raise DomainError('not_approved','Every other active profile must approve the current request',409,detail)
        # Preserve the revision reviewed by votes: lifecycle changes are still revisioned,
        # with approval history referenced by approved_revision after purchase.
        self.save(c,s.approval_requests,{'status':'purchased','purchase_id':op['entity_id'],'approved_revision':request['revision']},request)

    def do_comment_create(self,c,op):
        data=op['data'];get(c,s.RESOURCES[data['target_resource']],data['target_id'])
        result=self.save(c,s.comments,dict(id=op['entity_id'],actor_id=op['actor_id'],**data))
        self.notify(c,op,'comment.created',data['target_resource'],data['target_id'])
        return result

    def do_comment_resend(self,c,op):
        row=get(c,s.comments,op['entity_id'])
        if row['actor_id']!=op['actor_id']:
            raise DomainError('actor','Only the author can resend a comment notification',403)
        get(c,s.RESOURCES[row['target_resource']],row['target_id'])
        self.notify(c,op,'comment.created',row['target_resource'],row['target_id'])
        return row
