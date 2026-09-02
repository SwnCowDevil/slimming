const { request } = require("./client");
function listRecipes(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== "")
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join("&");
  return request({ url: `/api/v1/recipes${query ? `?${query}` : ""}` });
}
function recordRecipe(id,payload,key){return request({url:`/api/v1/recipes/${id}/record`,method:"POST",data:payload,headers:{"Idempotency-Key":key}});}
function favoriteRecipe(id){return request({url:`/api/v1/recipes/${id}/favorite`,method:"POST"});}
function unfavoriteRecipe(id){return request({url:`/api/v1/recipes/${id}/favorite`,method:"DELETE"});}
module.exports={listRecipes,recordRecipe,favoriteRecipe,unfavoriteRecipe};
