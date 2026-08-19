const { request } = require("./client");
function getProfile(){return request({url:"/api/v1/profiles/me"});}function saveWeight(recordedDate,weightKg){return request({url:"/api/v1/weights",method:"POST",data:{recorded_date:recordedDate,weight_kg:weightKg}});}
module.exports={getProfile,saveWeight};
