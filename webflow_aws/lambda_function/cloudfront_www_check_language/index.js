var path = require('path');

let VALID_LANGS = ["en"];
let DEFAULT_LANG = VALID_LANGS[0];

exports.handler = async (event) => {

  let request = event.Records[0].cf.request;
  let headers = event.Records[0].cf.request.headers;
  let uri = request.uri;
  let uriParts = uri.split("/");

  let lang = "";


  //TODO remove after all rect cached versions are expired
  // used to make sure all registered service worker of previous react vesion are then removed
  // one removed that, removed also all the following exception files from S3
  // this does not guarantee with old react will work
  // then remove also the clear-site-data in the generateRedirectResponse() function
  if (uriParts[1] === "asset-manifest.json" || uriParts[1] === "manifest.json" || uriParts[1] === "precache-manifest.e95fc79a3620d8ee2a5587047d6949fd.js" ||
  uriParts[1] === "service-worker.js" ||
  uriParts[1] === "static")  return event.Records[0].cf.request;

  if (VALID_LANGS.includes(uriParts[1])) {
      // it's a valid lang
      // if it's just the lang and it doesn't have a trailing slash, redirect with the trailing slash
      if (uriParts.length === 2) {
          let redirectUrl = "https://"+getHeader(headers, 'host')[0]['value']+uriParts.join("/")+"/";
          return generateRedirectResponse(redirectUrl);
      }
      //we have all correct to continue, we can let it go
      uriParts.splice(1,1);
      event.Records[0].cf.request.uri = uriParts.join("/");
      return event.Records[0].cf.request;
  } else {
      let langCookieSet = true;
      // we don't have the language, check if we have the cookie set
      let cookies_group = getHeader(headers, 'cookie');
      if (cookies_group) {
          for (let cg of cookies_group) {
              let breakLoop = false;
              // c can be something like "SomeCookie=1; AnotherOne=A; X-Experiment-Name=B" where each value is a cookie, so need to be split.
              // we can have multiple Cookie headers, this is why we have a look outside
              let cookie_array = cg['value'].split("; ");
              for (let c of cookie_array) {
                  let c_split = c.split("=");
                  let key = c_split[0];
                  let val = c_split[1];
                  if (key && key === "language" && val.length === 2) {
                      lang = val;
                      breakLoop = true;
                      break;
                  }
              }
              if (breakLoop) break;
          }
      }

      // if we don't have the cookie or it's not a valid lang, get the browser lang
      if (lang === "" || !VALID_LANGS.includes(lang)) {
          // set we don't have a valid cookie lang set
          langCookieSet = false;
          //get the accept-language header
          let acceptedLangs = getHeader(headers, 'accept-language');
          if (acceptedLangs) {
              //extract the langs
              let langs_acc = extractAcceptedLangs(acceptedLangs[0]['value']);

              //find the first accepted
              for (let l of langs_acc) {
                  if (VALID_LANGS.includes(l)) { lang = l; break; }
              }
          }
      }

      // if no lang has been set, set the default one
      if (lang === "") lang = DEFAULT_LANG;

      // prepare the redirect url
      if (uriParts[1].length===2) uriParts.splice(1,1);
      let redirectUrl = "https://"+getHeader(headers, 'host')[0]['value']+"/"+lang+uriParts.join("/");

      //set cookie response and redirect
      return generateRedirectResponse(redirectUrl, lang, !langCookieSet);
  }

};



/**
* Transform the string of accepted langs in an array of 2-letters accepted langs.
*
* @param {string} headerLangs - the string with all the langs accepted by the browser. Example:
*
* @return {string[]} - list of 2-letters string with the accepted languages
*
**/
let extractAcceptedLangs = (headerLangs) => {
  let re = new RegExp(/([A-Za-z]{2})(?!\-)|([A-Za-z]{2}\-[A-Za-z]{2})/g);
  let langs_acc = headerLangs.match(re);

  // get only first 2 chars if langs
  for (let i=0; i<langs_acc.length; i++) {
      if (langs_acc[i].length>2) {
          let lang_tmp = langs_acc[i].split("-");
          if (lang_tmp.length<2) langs_acc[i] = "";
          else langs_acc[i] = lang_tmp[1];
      }
  }

  //remove duplicates
  let tmpSet = new Set(langs_acc);
  langs_acc = [...tmpSet];

  // remove empy values
  langs_acc = langs_acc.filter((e) => e.length>0);

  return langs_acc;
}


/**
* Given the list of all the headers, return the one needed, or undefined
*
* @param {Objet[]} headers - list of all the headers (objects with "key" and "value" items)
* @param {string} key - the key are are looking for
*
* @return {string[] | undefined} The value searched, or undefined
*
**/
let getHeader = (headers, key) => {
  let header = headers[key];
  if (header && Array.isArray(header)) {
      return header;
  }
  return undefined;
}

/**
* Generates a redirect response.
*
* @param {string} redirectUrl - the redirect URL
* @param {string} cookieLang - the lang we would like to set in the cookie. If empty, the "set-cookie" is not returned
* @param {bool} clearSiteData - sent with true if a new user without cookie lang is received
*
*
* @return {Object} The response to be returned from this lambda function
*
**/
let generateRedirectResponse = (redirectUrl, cookieLang="", clearSiteData = false) => {

  let response = {
          status: '302',
          statusDescription: 'Found',
          headers: {
              'location': [{
                  key: 'location',
                  value: redirectUrl
              }]
          }
      };

  if (cookieLang) response.headers['set-cookie'] = [{
                                                      key: 'set-cookie',
                                                      value: 'language='+cookieLang+'; Path=/'
                                                  }];

  if (clearSiteData) response.headers['clear-site-data'] = [{
                                                      key: 'clear-site-data',
                                                      value: '*'
                                                  }];

  return response;
}