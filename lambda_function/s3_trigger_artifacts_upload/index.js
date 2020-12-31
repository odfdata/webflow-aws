const AWS = require('aws-sdk');
const util = require('util');
const AdmZip = require('adm-zip');

// get reference to S3 client
var s3 = new AWS.S3();
var cf = new AWS.CloudFront();

/**
 * Once a file is uploaded in the S3 bucket www.ianum under /artifacts/alpha or /artifacts/prod, that operation triggers this function.
 * The zip file is read, unzipped, moved the files in the /src/alpha (or /src/prod) folder, invalidated the related CDN and removed the
 * artifact file
 **/


exports.handler = async (event) => {

  let srcBucket = event.Records[0].s3.bucket.name;
  let srcKey    = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, " "));
  let dstBucket = event.Records[0].s3.bucket.name;
  console.log(srcBucket);
  console.log(srcKey);
  //alpha o prod?
  let stage = srcKey.split("/")[1] === PRODUCTION ? PRODUCTION : ALPHA;
  let dstFolder = "src/"+stage+"/";

  // prendo il file
  let zipData = await s3.getObject({
    Bucket: srcBucket,
    Key: srcKey
  }).promise();

  // unzip and upload the files
  let zip = new AdmZip(zipData.Body);
  var zipEntries = zip.getEntries(); // an array of ZipEntry records

  // uploads will go in parallel, with a Promise.all approach
  let promiseUploads = [];
  for (let zipEntry of zipEntries) {

    // replace all .html in the links
    let buf = zipEntry.getData();
    if (zipEntry.name.split(".").pop() === "html") {
      buf = await replaceHtmlLink(zipEntry.getData());
    }

    promiseUploads.push(s3.putObject({
      Body: buf,
      Bucket: dstBucket,
      Key: dstFolder + zipEntry.entryName,
      ContentType: getContentType(zipEntry.entryName),
      CacheControl: "public, max-age=3600",
    }).promise());
  }
  await Promise.all(promiseUploads);
  console.log(stage);
  console.log(getDistributionId(stage, srcBucket));
  // invalidate CDN
  await cf.createInvalidation({
    DistributionId: getDistributionId(stage, srcBucket),
    InvalidationBatch: {
      CallerReference: Date.now()+"",
      Paths: {
        Quantity: 1,
        Items: [
          "/*"
        ]
      }
    }
  }).promise();

  // remove artifacts
  await s3.deleteObject({
    Bucket: srcBucket,
    Key: srcKey
  }).promise();
  console.log("DONE");
};



/**
 * Transform a buffer to a string, replace the .html with noting, then recreates the buffer
 **/
async function replaceHtmlLink (buffData) {
  let utf8String = buffData.toString('utf8');
  utf8String = utf8String.replace(/\.html(?!\?)/g, '');
  return Buffer.from(utf8String, 'utf8');
}


/**
 * Given a filename, returns a valid content type for that extension
 **/
function getContentType (fileName) {
  let ext = fileName.split(".").pop();
  let contentType = "";
  switch (ext) {
    case 'html':
      contentType = "text/html";
      break;
    case 'jpg':
    case 'jpeg':
      contentType = "image/jpeg";
      break;
    case "png":
      contentType = "image/png";
      break;
    case "js":
      contentType = "application/javascript";
      break;
    case "css":
      contentType = "text/css";
      break;
    case "svg":
      contentType = "image/svg+xml";
      break;
    case "ico":
      contentType = "image/x-icon";
      break;
    default:
      contentType = "application/octet-stream";
  }

  return contentType;
}
