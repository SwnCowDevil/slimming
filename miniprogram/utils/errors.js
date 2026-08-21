function requestErrorMessage(error) {
  const detail = error && error.data && error.data.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (detail && typeof detail === "object" && typeof detail.message === "string") {
    return detail.message;
  }

  if (error && error.errMsg) {
    return "网络连接失败，请检查后端服务";
  }

  return "暂时无法保存，请重试";
}

module.exports = { requestErrorMessage };
