var path = require('path');

exports.handler = async (event) => {

  let uri = event.Records[0].cf.request.uri;
  let uriParts = uri.split("/");

  let index_uriPartsLastItem = uriParts.length - 1;
  let uriFileName = uriParts[index_uriPartsLastItem];

  if (uriFileName==="") uriParts[index_uriPartsLastItem] = "index.html";
  else {
      let ext = path.extname(uriParts[index_uriPartsLastItem]);
      if (ext === "") uriParts[index_uriPartsLastItem] = uriParts[index_uriPartsLastItem] + ".html";
  }

  uri = uriParts.join("/");
  event.Records[0].cf.request.uri = uri;

  return event.Records[0].cf.request;
};