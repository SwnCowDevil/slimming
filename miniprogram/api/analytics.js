const {request}=require("./client");function getSummary(period,endDate){return request({url:`/api/v1/analytics/summary?period=${period}&end_date=${endDate}`});}module.exports={getSummary};
