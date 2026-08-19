const { request } = require("./client");
function createDraft(data){return request({url:"/api/v1/ai/drafts",method:"POST",data});}function confirmDraft(id,key){return request({url:`/api/v1/ai/drafts/${id}/confirm`,method:"POST",headers:{"Idempotency-Key":key}});}
module.exports={createDraft,confirmDraft};
