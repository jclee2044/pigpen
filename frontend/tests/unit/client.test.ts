import { describe,it,expect,vi,afterEach } from 'vitest'
import { request,execute,operation,ApiError } from '../../src/api/client'
import { parseMoney,inputMoney } from '../../src/lib/money'
afterEach(()=>vi.unstubAllGlobals())
describe('money boundary',()=>{
 it('uses exact cents and rejects ambiguous input',()=>{expect(parseMoney('0.29')).toBe(29);expect(inputMoney(123)).toBe('1.23');for(const value of ['1.001','1,2','-1','1e5',''])expect(()=>parseMoney(value)).toThrow()})
})
describe('API contract',()=>{
 it('preserves the complete operation across retries',async()=>{const fetcher=vi.fn().mockResolvedValue(new Response('{}',{status:200}));vi.stubGlobal('fetch',fetcher);const op=operation('purchase.delete',{expected_revision:1},crypto.randomUUID());await execute(op);fetcher.mockResolvedValueOnce(new Response('{}',{status:200}));await execute(op);expect(fetcher.mock.calls[0]![1].body).toBe(fetcher.mock.calls[1]![1].body)})
 it('preserves actionable conflicts',async()=>{vi.stubGlobal('fetch',vi.fn().mockResolvedValue(new Response(JSON.stringify({error:{code:'revision_conflict',message:'Review changes',details:{revision:2}}}),{status:409})));await expect(request('/operations')).rejects.toMatchObject({status:409,code:'revision_conflict',details:{revision:2}})})
 it('reports network failures without financial payloads',async()=>{vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new Error('sensitive internal error')));await expect(request('/household')).rejects.toBeInstanceOf(ApiError);await expect(request('/household')).rejects.not.toThrow('sensitive')})
})
