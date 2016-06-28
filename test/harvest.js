const jsdom = require('jsdom');
const path = require('path');


class Processor {
   process(uri) {
      let isfile = uri.startsWith("file://")
      jsdom.env({[isfile ? "file" : "url"]: isfile ? uri.substring(7) : uri, done: (err,window) => { if (err) { console.log(err) } else this.harvest(window.document)} });
   }

   harvest(document) {
      console.log(document.baseURI)
   }
}

let proc = new Processor()
let [,, ... args] = process.argv;
for (let file of args) {
   let uri = file.startsWith("http:") ||
             file.startsWith("https:") ||
             file.startsWith("file:") ? file : "file://" + path.resolve(process.cwd(),file);
   proc.process(uri);
}
