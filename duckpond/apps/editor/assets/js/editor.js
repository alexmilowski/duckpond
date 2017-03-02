function SafeHTML(templateData) {
  var s = templateData[0];
  for (var i = 1; i < arguments.length; i++) {
    var arg = String(arguments[i]);

    // Escape special characters in the substitution.
    s += arg.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");

    // Don't escape special characters in the template.
    s += templateData[i];
  }
  return s;
}

function localDateTime() {
    var now = new Date(),
        tzo = -now.getTimezoneOffset(),
        dif = tzo >= 0 ? '+' : '-',
        pad = function(num) {
            var norm = Math.abs(Math.floor(num));
            return (norm < 10 ? '0' : '') + norm;
        };
    return now.getFullYear()
        + '-' + pad(now.getMonth()+1)
        + '-' + pad(now.getDate())
        + 'T' + pad(now.getHours())
        + ':' + pad(now.getMinutes())
        + ':' + pad(now.getSeconds())
        + dif + pad(tzo / 60)
        + ':' + pad(tzo % 60);
}

function parseDateTime(dateTime) {
   let tpos = dateTime.indexOf('T');
   let date = dateTime.substring(0,tpos);
   let time = dateTime.substring(tpos+1);
   let period = time.indexOf('.',time.indexOf(':',time.indexOf(':')+1))
   if (period>0) {
      let dash = time.indexOf('-',period);
      if (dash>0) {
         time = time.substring(0,period)+time.substring(dash);
      }
   }
   return [date,time];

}

class DuckpondEditor {
   constructor(client) {
      this.client = client;
      this.content = {};
      this.inputTypes = {
         "description": "textarea"
      }
   }

   inputTypeFor(property) {
      let type = this.inputTypes[property];
      return type==undefined ? "input" : type;
   }

   bind() {
      fetch("/config.json",{credentials: 'include'}).then(
         (response) => {
            if (response.ok) {
               response.json().then((data) => {
                  this.config = data;
               });
            } else {
               this.error(`Cannot get configuration, status=${response.status}`);
            }
         }
      );
      $("#editor-create-content").click(
         (e) => {
            let genreInput = $("#editor-form-content-create input[name=genre]");
            let genre = genreInput.val().trim();
            let nameInput = $("#editor-form-content-create input[name=name]");
            let name = nameInput.val().trim();
            let typeInput = $("#editor-form-content-create input[name=type]");
            let type = typeInput.val().trim();
            let titleInput = $("#editor-form-content-create input[name=title]");
            let title = titleInput.val().trim();
            let valid = true;
            if (genre=="") {
               genreInput.addClass("uk-form-danger")
               valid = false;
            } else {
               genreInput.removeClass("uk-form-danger")
            }
            if (name=="") {
               nameInput.addClass("uk-form-danger")
               valid = false;
            } else {
               nameInput.removeClass("uk-form-danger")
            }
            if (title=="") {
               titleInput.addClass("uk-form-danger")
               valid = false;
            } else {
               titleInput.removeClass("uk-form-danger")
            }
            if (type=="") {
               typeInput.addClass("uk-form-danger")
               valid = false;
            } else {
               typeInput.removeClass("uk-form-danger")
            }
            if (valid) {
               this.createContent(type,genre,name,title);
            }
         }
      );
      $("#editor-form-content-create select").change(() => {
         $("#editor-form-content-create input[name=type]")[0].value = $("#editor-form-content-create select").val();
      });
      $(".editor-reload-content").click(
         (e) => {
            this.reloadContents();
         }
      );
      $("#editor-add-part-dialog select").change(() => {
         $("#editor-add-part-dialog input[name=type]")[0].value = $("#editor-add-part-dialog select").val();
      });
   }

   error(message) {
      this.notify("Woah!",message);
   }

   notify(title,message) {
      $("#editor-notify-title").text(title)
      $("#editor-notify-message").text(message)
      UIkit.modal("#editor-notify")[0].toggle()
   }

   login(onSuccess) {
      console.log("Showing login dialog...");
      UIkit.modal("#editor-login-dialog")[0].toggle();
      let iframe = $("<iframe src='/login?compact=true&redirect=false'></iframe>");
      $("#editor-login-dialog-contents").append(iframe);
      let loginPoll = () => {
         if (iframe[0].contentWindow.username != undefined) {
            $("#editor-login-dialog-contents").empty();
            UIkit.modal("#editor-login-dialog")[0].toggle();
            if (onSuccess!=undefined) {
               setTimeout(onSuccess,10);
            }
         } else {
            setTimeout(loginPoll,500);
         }
      };
      loginPoll();
   }

   reloadContents() {
      this.client.getContents().then((contents) => {
         console.log("Refreshing content display...")

         $("#editor-content-genre-list li").remove();

         this.genres = {};
         let sortedGenres = [];
         for (let content of contents) {
            let genre = this.genres[content.genre];
            if (genre==undefined) {
               genre = {
                  items: []
               };
               this.genres[content.genre] = genre;
               sortedGenres.push(content.genre);
            }
            genre.items.push(content);
         }
         sortedGenres.sort()

         for (let [index,genre] of sortedGenres.entries()) {
            let def = this.genres[genre];
            def.container = $(
               `<li class="${index==0 ? 'uk-open' : ''}">
                  <h3 class="uk-accordion-title">${genre}</h3>
                  <div class="uk-accordion-content uk-overflow-auto" data-genre="${genre}">
                     <table class="uk-table uk-table-striped uk-table-condensed uk-text-nowrap">
                        <tr><th></th><th>Name</th><th>Date</th><th>Time</th><th>Type</th><th>Headline</th><td></td></tr>
                     </table>
                  </div>
                </li>`
            );
            $("#editor-content-genre-list").append(def.container);
            def.items.sort(function(a,b) {
               let v = a['dateModified'].localeCompare(b['dateModified']);
               return v<0 ? 1 : v>0 ? -1 : 0;
            })
            for (let content of def.items) {
               let [date,time] = parseDateTime(content.dateModified);
               $(def.container).find("table").append(
                  `<tr class="content-row"
                       data-url="${content.url}"
                       data-genre="${content.genre}"
                       data-name="${content.name}"
                       data-type="${content['@type']}"
                       data-headline="${content.headline}"
                       data-modified="${content.dateModified}">
                   <td class="toolbar">
                      <ul class="uk-iconnav">
                      <li><a href="#" class="uk-icon-link editor-edit-content" uk-icon="icon: file-edit" title="edit"></a></li>
                      <li><a href="#" class="uk-icon-link editor-delete-content" uk-icon="icon: trash" title="delete"></a></li>
                      </ul>
                   </td>
                   <td class="name">${content.name}</td>
                   <td class="date">${date}</td>
                   <td class="time">${time}</td>
                   <td class="type">${content['@type']}</td>
                   <td class="headline">${content.headline}</td>
                   <td></td>
                   </tr>`
               )
            }
         }

         $(".editor-edit-content").click(
            (e) => {
               this.editContent($(e.currentTarget).closest("tr").get(0).dataset);
            }
         );
         $(".editor-delete-content").click(
            (e) => {
               let row = $(e.currentTarget).closest("tr").get(0);
               this.deleteContent(row,row.dataset);
            }
         );

         console.log("Finished.")
      }).catch((status) => {
         if (status==401) {
            console.log("Login expired...");
            this.login();
         } else {
            this.error(`Cannot load content, status ${status}`);
         }
      })
   }

   createGenreDefinition(genre) {
      let def = this.genres[genre];
      if (def==undefined) {
         def = { items: [] };
         this.genres[genre] = def;
         def.container = $(
            `<li>
               <h3 class="uk-accordion-title">${genre}</h3>
               <div class="uk-accordion-content uk-overflow-auto" data-genre="${genre}">
                  <table class="uk-table uk-table-striped uk-table-condensed uk-text-nowrap">
                     <tr><th></th><th>Name</th><th>Date</th><th>Time</th><th>Type</th><th>Headline</th><td></td></tr>
                  </table>
               </div>
             </li>`
         );
         let appended = false;
         $("#editor-content-genre-list li div").each((i,div) => {
            if (!appended && div.dataset.genre > genre) {
               def.container.insertBefore($(div.parentNode))
               appended = true;
            }
         });
         if (!appended) {
            $("#editor-content-genre-list").append(def.container);
         }
      }
      return def;

   }

   createContent(typeName,genre,name,title) {
      this.client.createContent(typeName,genre,name,title)
         .then((response) => {
            console.log(response.location+" "+response.modified);
            let def = this.createGenreDefinition(genre);
            let [date,time] = parseDateTime(response.modified);
            // Create the row
            let row = $(
               `<tr class="content-row"
                    data-url="${response.location}"
                    data-genre="${genre}"
                    data-name="${name}"
                    data-type="${typeName}"
                    data-headline="${title}"
                    data-modified="${response.modified}">
                <td class="toolbar">
                   <ul class="uk-iconnav">
                   <li><a href="#" class="uk-icon-link editor-edit-content" uk-icon="icon: file-edit" title="edit"></a></li>
                   <li><a href="#" class="uk-icon-link editor-delete-content" uk-icon="icon: trash" title="delete"></a></li>
                   </ul>
                </td>
                <td class="name">${name}</td>
                <td class="date">${date}</td>
                <td class="time">${time}</td>
                <td class="type">${typeName}</td>
                <td class="headline">${title}</td>
                <td></td>
                </tr>`
            )

            let rowAppended = false;
            def.container.find("table tr").each((i,currentRow) => {
               if (!rowAppended && currentRow.dataset.modified < response.modified) {
                  row.insertBefore($(currentRow));
                  rowAppended = true;
               }
            });
            if (!rowAppended) {
               def.container.find("table").append(row);
            }

            // Attach the actions for the row
            row.find(".editor-edit-content").click(
               (e) => {
                  this.editContent($(e.currentTarget).closest("tr").get(0).dataset);
               }
            );
            row.find(".editor-delete-content").click(
               (e) => {
                  let row = $(e.currentTarget).closest("tr").get(0);
                  this.deleteContent(row,row.dataset);
               }
            );

            // Switch to the content tab
            UIkit.switcher("#editor-content-tabs")[0].show(1);
         })
         .catch((status) => {
            if (status==401) {
               console.log("Login expired...");
               this.login();
            } else if (status==409) {
               this.notify("Conflicting Content",`A content item with genre "${genre}" and name "${name}" already exists`);
            } else {
               this.error(`Cannot create content, status ${status}`);
            }
         });

   }

   updateContentItem(oldGenre,oldName,newGenre,newName,headline,modified) {
      console.log(oldGenre+"/"+oldName+" -> "+newGenre+"/"+newName);
      let row = undefined;
      let divContainer = undefined;
      $("#editor-content-genre-list li div").each((i,div) => {
         if (div.dataset.genre==oldGenre) {
            divContainer = div
         }
      });
      $(divContainer).find("table tr").each((i,tr) => {
         if (tr.dataset.name==oldName) {
            row = tr;
         }
      })
      if (oldGenre!=newGenre) {
         $(row).remove();
         let count = 0;
         $(divContainer).find("table tr").each((i,row) => {
            count++;
         });
         if (count<=1) {
            $(divContainer.parentNode).remove();
         }
         let def = this.createGenreDefinition(newGenre);
         let rowAppended = false;
         def.container.find("table tr").each((i,currentRow) => {
            if (!rowAppended && currentRow.dataset.modified < modified) {
               $(row).insertBefore($(currentRow));
               rowAppended = true;
            }
         });
         if (!rowAppended) {
            def.container.find("table").append(row);
         }
         // Attach the actions for the row
         $(row).find(".editor-edit-content").click(
            (e) => {
               this.editContent($(e.currentTarget).closest("tr").get(0).dataset);
            }
         );
         $(row).find(".editor-delete-content").click(
            (e) => {
               let r = $(e.currentTarget).closest("tr").get(0);
               this.deleteContent(r,r.dataset);
            }
         );

      }
      $(row).attr("data-genre",newGenre);
      $(row).attr("data-name",newName);
      $(row).attr("data-headline",headline);
      $(row).attr("data-modified",modified);
      let [date,time] = parseDateTime(modified);
      $(row).find(".name").text(newName);
      $(row).find(".date").text(date);
      $(row).find(".time").text(time);
      $(row).find(".headline").text(headline);
      $("#editor-content-tabs li").each((i,tab) => {
         if (tab.dataset['url']==row.dataset['url']) {
            $(tab).find(".label").text(newGenre+" / "+newName);
         }
      });
   }


   contentIdFromURL(url) {
      let idMatch = url.match(/\/([^\/]+)\/$/);
      if (!idMatch) {
         return undefined;
      }
      return idMatch[1];
   }

   editContent(dataset) {
      let id = this.contentIdFromURL(dataset.url);
      if (!id) {
         this.error(`Cannot parse content URI ${dataset.url}`);
         return;
      }

      let found = false;
      $("#editor-content-tabs li").each((i,tab) => {
         if (tab.dataset['url']==dataset['url']) {
            UIkit.switcher("#editor-content-tabs")[0].show(i);
            found = true;
         }
      });
      if (found) return;

      let tabContent = $(
         SafeHTML`<li data-url="${dataset.url}" class="editor-content-tab-item">
            <ul class="uk-iconnav uk-iconnav-vertical editor-content-item-menu">
               <li><a href="#" uk-icon="icon: close" title="Close" class="editor-content-item-close"></a></li>
               <li><a href="#" uk-icon="icon: refresh" title="Refresh" class="editor-content-item-refresh"></a></li>
               <li><a href="#" uk-icon="icon: push" title="Save" class="editor-content-item-save"></a></li>
            </ul>
            <div class="editor-content-item" id="content-item-${id}">
               <p>Loading ...</p>
            </div>
         </li>`
      );
      let tab = $(
         SafeHTML`<li data-url="${dataset.url}" class="editor-content-tab uk-visible-toggle"><a href="#" title="${dataset.headline}"><span class="uk-icon-link uk-invisible-hover editor-closer" uk-icon="icon: close; ratio: 0.75"></span><span class="label">${dataset.genre} / ${dataset.name}</span></a></li>`
      );
      let tabIndex = $("#editor-content-tabs li").length;
      $("#editor-content-tabs").append(tab);
      $("#editor-content").append(tabContent);
      tabContent.find(".editor-content-item-close").click((e) => {
         tab.remove();
         tabContent.remove();
         UIkit.switcher("#editor-content-tabs")[0].show(tabIndex-1);
      });
      tab.find(".editor-closer").click((e) => {
         tab.remove();
         tabContent.remove();
         UIkit.switcher("#editor-content-tabs")[0].show(tabIndex-1);
      });
      tabContent.find(".editor-content-item-refresh").click((e) => {
         let contentItem = tabContent.find(".editor-content-item");
         this.client.getContent(id)
            .then((data) => {
               console.log(data);
               contentItem.empty();
               this.addContentEdit(id,data,tabContent)
            })
            .catch((status) => {
               if (status==401) {
                  console.log("Login expired...");
                  this.login();
               } else {
                  this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
               }
            })
      });
      setTimeout(
         () => {
            UIkit.switcher("#editor-content-tabs")[0].show(tabIndex);
         },
         50
      );
      //tabContent.find(".editor-content-item")
      this.client.getContent(id)
         .then((data) => {
            //console.log(data);
            this.addContentEdit(id,data,tabContent)
         })
         .catch((status) => {
            if (status==401) {
               console.log("Login expired...");
               this.login();
            } else {
               this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
            }
         })
   }

   updateModified(item,dateModified) {
      let [date,time] = dateModified.split("T");
      $(item).find(".editor-property-date-modified").text(date);
      $(item).find(".editor-property-time-modified").text(time);
   }

   addContentEdit(id,data,tabContent) {
      let info = {
         id : id,
         ld : data,
         ui : tabContent,
         parts : []
      };
      this.content[id] = info;
      let contentItem = tabContent.find(".editor-content-item");
      contentItem.find("*").remove();
      let header = $(SafeHTML`
         <div class="uk-card uk-card-default uk-card-body">
         <h3 class="uk-heading-line"><span>${data["@type"]}</span></h3>
         <p>modified on <span class="editor-property-date-modified"></span> at <span class="editor-property-time-modified"></span></p>
         </div>`)
      contentItem.append(header);
      this.updateModified(header,data["dateModified"]);
      let properties = $(SafeHTML`
         <div class="uk-card uk-card-default uk-card-body uk-margin editor-properties">
         <h3 class="uk-heading-line"><span>Properties</span></h3>
         <ul uk-tab>
            <li class="uk-active">
               <a href="#">Standard</a>
            </li>
            <li class="uk-active">
               <a href="#">Extended</a>
            </li>
         </ul>
         <ul class="uk-switcher uk-margin">
         <li>
            <div class="uk-card uk-margin-left uk-margin-right editor-properties-standard">
               <fieldset class="uk-fieldset  uk-form-horizontal">
                  <div class="uk-margin">
                     <label class="uk-form-label" for="genre">Genre</label>
                     <div class="uk-form-controls">
                        <input class="uk-input" value="${data["genre"]}" name="genre" size="40">
                     </div>
                  </div>
                  <div class="uk-margin">
                     <label class="uk-form-label" for="genre">Name</label>
                     <div class="uk-form-controls">
                        <input class="uk-input" value="${data["name"]}" name="name" size="40">
                     </div>
                  </div>
                  <div class="uk-margin">
                     <label class="uk-form-label" for="genre">Title</label>
                     <div class="uk-form-controls">
                        <input class="uk-input" value="${data["headline"]}" name="headline" size="40">
                     </div>
                  </div>
                  <div class="uk-margin">
                     <label class="uk-form-label" for="genre">Description</label>
                     <div class="uk-form-controls">
                        <textarea class="uk-textarea" name="description" cols="40" rows="5">${"description" in data ? data["description"] : ""}</textarea>
                     </div>
                  </div>
                  <div class="uk-margin">
                     <label class="uk-form-label" for="genre">Date Published</label>
                     <div class="uk-form-controls">
                        <button class="uk-button uk-button-default editor-publish">Publish</button>
                        <input class="uk-input" value="${"datePublished" in data ? data["datePublished"] : ""}" name="datePublished" size="40">
                     </div>
                  </div>
                  <div class="uk-margin">
                     <label class="uk-form-label" for="genre">Keywords</label>
                     <div class="uk-form-controls">
                        <textarea class="uk-textarea" name="keywords" cols="40" rows="2">${"keywords" in data ? data["keywords"] : ""}</textarea>
                     </div>
                  </div>
               </fieldset>
            </div>
         </li>
            <div class="uk-card uk-margin-left uk-margin-right uk-form-horizontal editor-properties-extended">
               <div class="uk-card uk-card-default uk-card-body editor-part-editor">
               <h3 class="uk-heading-line"><span>Additional JSON-LD</span></h3>
               <textarea class="uk-textarea" name="additionalld" rows="15"></textarea>
               </div>
            </div>
         </ul>`);
      contentItem.append(properties);
      $(properties).find(".editor-publish").click(() => {
         properties.find(".uk-input[name=datePublished]").val(localDateTime());
      })
      let propertiesBody = properties.find(".editor-properties-standard");

      tabContent.find(".editor-content-item-save").off("click");
      tabContent.find(".editor-content-item-save").click((e) => {
         let genre = propertiesBody.find(".uk-input[name=genre]").val().trim();
         let name = propertiesBody.find(".uk-input[name=name]").val().trim();
         let headline = propertiesBody.find(".uk-input[name=headline]").val().trim();
         let description = propertiesBody.find("textarea[name=description]").val().trim();
         let datePublished = propertiesBody.find(".uk-input[name=datePublished]").val().trim();
         let keywordsText = propertiesBody.find("textarea[name=keywords]").val().trim();
         let valid = true;
         if (genre=="") {
            propertiesBody.find(".uk-input[name=genre]").addClass("uk-form-danger");
            valid = false;
         } else {
            propertiesBody.find(".uk-input[name=genre]").removeClass("uk-form-danger");
         }
         if (name=="") {
            propertiesBody.find(".uk-input[name=name]").addClass("uk-form-danger");
            valid = false;
         } else {
            propertiesBody.find(".uk-input[name=name]").removeClass("uk-form-danger");
         }
         if (headline=="") {
            propertiesBody.find(".uk-input[name=headline]").addClass("uk-form-danger");
            valid = false;
         } else {
            propertiesBody.find(".uk-input[name=headline]").removeClass("uk-form-danger");
         }
         if (!valid) {
            return;
         }
         let currentGenre = info.ld["genre"];
         let currentName = info.ld["name"];
         info.ld["genre"] = genre;
         info.ld["name"] = name;
         info.ld["headline"] = headline;
         if (description=="") {
            delete info.ld["description"]
         } else {
            info.ld["description"] = description;
         }
         if (datePublished=="") {
            delete info.ld["datePublished"]
         } else {
            info.ld["datePublished"] = datePublished;
         }
         if (keywordsText=="") {
            delete info.ld["keywords"]
         } else {
            let keywords = keywordsText.split(",");
            for (let i in keywords) {
               keywords[i] = keywords[i].trim();
            }
            info.ld["keywords"] = keywords;
         }
         console.log(info.ld);
         this.client.updateContent(info.id,info.ld)
            .then((updatedData) => {
               UIkit.notification("<span uk-icon='icon: check'></span> Properties saved.");
               info.ld["dateModified"] = updatedData["dateModified"];
               this.updateModified(header,updatedData["dateModified"]);
               this.updateContentItem(currentGenre,currentName,genre,name,headline,info.ld["dateModified"])
            })
            .catch((status) => {
               if (status==401) {
                  console.log("Login expired...");
                  this.login();
               } else if (status==409) {
                  this.notify('Conflicting Genre / Name',`The genre "${genre}" and name "${name}" are in use.`);
               } else {
                  this.error(`Cannot update properties ${info.id}, status ${status}`);
               }
            });
      });

      let partList = [];
      let mediaList = [];
      for (let property of Object.keys(data)) {
         if (property=="@context" || property=="@id" || property=="@type" || property=="dateModified" || property=="url" || property=="author") {
            continue;
         } else if (property=="hasPart"){
            partList = data[property]
         } else if (property=="associatedMedia"){
            mediaList = data[property]
         }
      }
      let footer = $(SafeHTML`
         <div class="uk-child-width-expand uk-margin" uk-grid>
           <div>
             <div class="uk-card uk-card-default uk-card-body">
                <h3 class="uk-heading-line"><span>Parts</span></h3>
                <ul class="uk-list editor-content-parts">
                </ul>
                <ul class="uk-iconnav editor-content-part-menu">
                <li><a href="#" uk-icon="icon: plus" title="Create Part" class="editor-content-part-create"></a></li>
                </ul>
                <div class="editor-content-part-add uk-placeholder uk-text-center">
                  <span uk-icon="icon: cloud-upload"></span>
                  <span class="uk-text-middle">Add or update content by dropping them here or</span>
                  <div uk-form-custom>
                    <input type="file">
                    <span class="uk-link">selecting one</span>
                  </div>
                </div>
                <progress class="editor-content-part-add-progress" class="uk-progress" value="0" max="100" hidden></progress>
             </div>
           </div>
           <div>
             <div class="uk-card uk-card-default uk-card-body">
                <h3 class="uk-heading-line"><span>Media</span></h3>
                <ul class="uk-list editor-content-media">
                </ul>
                <div class="editor-content-media-add uk-placeholder uk-text-center">
                  <span uk-icon="icon: cloud-upload"></span>
                  <span class="uk-text-middle">Add or update media by dropping them here or</span>
                  <div uk-form-custom>
                    <input type="file">
                    <span class="uk-link">selecting one</span>
                  </div>
                </div>
                <progress class="editor-content-media-add-progress" class="uk-progress" value="0" max="100" hidden></progress>
           </div>
         </div>`);
      contentItem.append(footer);
      footer.find(".editor-content-part-create").click(() => {
         console.log("Add part");
         console.log(info);
         UIkit.modal("#editor-add-part-dialog")[0].toggle()
         return false;
      })
      let contentPartList = footer.find(".editor-content-parts");
      let addPart = (name,contentType) => {
         let item = $(SafeHTML`
            <li data-name="${name}">${name}; ${contentType}
               <a href="#" uk-icon="icon: file-edit" title="Edit Part" class="uk-icon-link editor-content-part-edit"></a>
               <a href="#" uk-icon="icon: download" title="Download (raw) Part" class="uk-icon-link editor-content-part-download"></a>
               <a href="#" uk-icon="icon: pull" title="Download (formatted) Part" class="uk-icon-link editor-content-part-download-formatted"></a>
               <a href="#" uk-icon="icon: play" title="Preview Part" class="uk-icon-link editor-content-part-preview"></a>
               <a href="#" uk-icon="icon: trash" title="Delete Part" class="uk-icon-link editor-content-part-delete"></a>
            </li>
         `);
         contentPartList.append(item);
         item.find(".editor-content-part-edit").click(() => {
            console.log(`Edit part ${name}`);
            this.editContentPart(info,name,contentType,false);
            return false;
         });
         item.find(".editor-content-part-download").click(() => {
            console.log(`Download part ${name}`);
            open(`/data/content/${info.id}/${name}`,name);
            return false;
         });
         item.find(".editor-content-part-download-formatted").click(() => {
            console.log(`Download part ${name}`);
            open(`/data/content/${info.id}/${name}?wrap=formatted`,name);
            return false;
         });
         item.find(".editor-content-part-preview").click(() => {
            console.log(`Download part ${name}`);
            open(`/data/content/${info.id}/${name}?wrap=preview`,name);
            return false;
         });
         item.find(".editor-content-part-delete").click(() => {
            setTimeout(() => {
               this.deleteContentPart(item,info,name);
            },25);
            return false;
         });
      };
      for (let part of partList) {
         addPart(part["name"],part["fileFormat"])
      }

      $("#editor-add-part-dialog .editor-create").off('click');
      $("#editor-add-part-dialog .editor-create").click(() => {
         let name = $("#editor-add-part-dialog input[name=name]").val();
         let type = $("#editor-add-part-dialog input[name=type]").val();
         if (name.trim()=="") {
            $("#editor-add-part-dialog input[name=name]").addClass("uk-form-danger");
            $("#editor-add-part-dialog .editor-message-name").text("Please enter a name.")
            return;
         } else {
            $("#editor-add-part-dialog .editor-message-name").text("")
            $("#editor-add-part-dialog input[name=name]").removeClass("uk-form-danger");
         }
         if (type.trim()=="") {
            $("#editor-add-part-dialog input[name=type]").addClass("uk-form-danger");
            $("#editor-add-part-dialog .editor-message-type").text("Please enter a media type.")
            return;
         } else {
            $("#editor-add-part-dialog .editor-message-type").text("")
            $("#editor-add-part-dialog input[name=type]").removeClass("uk-form-danger");
         }
         UIkit.modal("#editor-add-part-dialog")[0].toggle()
         setTimeout(() => {
            this.editContentPart(info,name.trim(),type.trim(),true,
               (name,contentType,creating) => {
                  if (creating) {
                     addPart(name,contentType);
                  }
               }
            );
         },10);
      })

      // Content Part Upload
      let contentBar = footer.find(".editor-content-part-add-progress")[0];
      UIkit.upload(`#content-item-${info.id} .editor-content-part-add`,{
         url : this.client.service + "content/" + info.id + "/upload/hasPart",
         multiple: false,
         name: "file",
         "data-type": "json",
         beforeSend: function() { console.log('beforeSend', arguments); },
         beforeAll: function() { console.log('beforeAll', arguments); },
         load: function() { console.log('load', arguments); },
         error: function() { console.log('error', arguments); },
         complete: function() { console.log('complete', arguments); },
         loadStart: function (e) {
            console.log('loadStart', arguments);

            contentBar.removeAttribute('hidden');
            contentBar.max =  e.total;
            contentBar.value =  e.loaded;
         },
         progress: function (e) {
            console.log('progress', arguments);

            contentBar.max =  e.total;
            contentBar.value =  e.loaded;
         },
         loadEnd: function (e) {
            console.log('loadEnd', arguments);

            contentBar.max =  e.total;
            contentBar.value =  e.loaded;
         },
         completeAll: function () {
            console.log('completeAll', arguments);

            console.log(arguments[0].responseJSON);

            let name = arguments[0].responseJSON["name"];
            let existing = false;
            contentPartList.find("li").each((i,item) => {
               if (item.dataset.name==name) {
                  existing = true;
               }
            });
            if (!existing) {
               addPart(name,arguments[0].responseJSON["fileFormat"]);
               if (info.ld.hasPart==undefined) {
                  info.ld.hasPart = [];
               }
               info.ld.hasPart.push(arguments[0].responseJSON);
               console.log(info.ld);
            }

            setTimeout(function () {
               contentBar.setAttribute('hidden', 'hidden');
            }, 1000);

            UIkit.notification("<span uk-icon='icon: check'></span> Media upload completed.");
         }
      });

      // Media List

      let contentMediaList = footer.find(".editor-content-media");
      let addMedia = (name,contentType) => {
         let item = $(SafeHTML`
            <li data-name="${name}">${name}; ${contentType}
               <a href="#" uk-icon="icon: download" title="Download Media" class="uk-icon-link editor-content-media-download"></a>
               <a href="#" uk-icon="icon: trash" title="Delete Media" class="uk-icon-link editor-content-media-delete"></a>
            </li>
         `);
         contentMediaList.append(item);
         item.find(".editor-content-media-download").click(() => {
            console.log(`Download media ${name}`);
            open(`/data/content/${info.id}/${name}`,name);
            return false;
         });
         item.find(".editor-content-media-delete").click(() => {
            setTimeout(() => {
               this.deleteContentMediaResource(item,info,name);
            },25);
            return false;
         });
      };
      for (let media of mediaList) {
         addMedia(media["name"],media["fileFormat"]);
      }
      let bar = footer.find(".editor-content-media-add-progress")[0];
      UIkit.upload(`#content-item-${info.id} .editor-content-media-add`,{
         url : this.client.service + "content/" + info.id + "/upload/associatedMedia",
         multiple: false,
         name: "file",
         "data-type": "json",
         beforeSend: function() { console.log('beforeSend', arguments); },
         beforeAll: function() { console.log('beforeAll', arguments); },
         load: function() { console.log('load', arguments); },
         error: function() { console.log('error', arguments); },
         complete: function() { console.log('complete', arguments); },
         loadStart: function (e) {
            console.log('loadStart', arguments);

            bar.removeAttribute('hidden');
            bar.max =  e.total;
            bar.value =  e.loaded;
         },
         progress: function (e) {
            console.log('progress', arguments);

            bar.max =  e.total;
            bar.value =  e.loaded;
         },
         loadEnd: function (e) {
            console.log('loadEnd', arguments);

            bar.max =  e.total;
            bar.value =  e.loaded;
         },
         completeAll: function () {
            console.log('completeAll', arguments);

            console.log(arguments[0].responseJSON);

            let name = arguments[0].responseJSON["name"];
            let existing = false;
            contentMediaList.find("li").each((i,item) => {
               if (item.dataset.name==name) {
                  existing = true;
               }
            });
            if (!existing) {
               addMedia(name,arguments[0].responseJSON["fileFormat"]);
               if (info.ld.associatedMedia==undefined) {
                  info.ld.associatedMedia = [];
               }
               info.ld.associatedMedia.push(arguments[0].responseJSON);
               console.log(info.ld);
            }

            setTimeout(function () {
               bar.setAttribute('hidden', 'hidden');
            }, 1000);

            UIkit.notification("<span uk-icon='icon: check'></span> Media upload completed.");
         }
      });

   }

   editContentPart(info,name,contentType,creating,onUpdate) {
      // Check to see if it is already open.  If so, switch to that tab.
      let baseContentType = contentType.indexOf(";")>0 ? contentType.substring(0,contentType.indexOf(";")) : contentType;
      let found = false;
      $("#editor-content-tabs li").each((i,tab) => {
         if (tab.dataset.id==info.id && tab.dataset.name==name) {
            setTimeout(
               () => {
                  UIkit.switcher("#editor-content-tabs")[0].show(i);
               },
               50
            );
            found = true;
         }
      });
      if (found) {
         return;
      }

      // Create a new tab with the content

      let tab = $(
         SafeHTML`<li data-id="${info.id}" data-name="${name}" class="editor-content-tab uk-visible-toggle"><a href="#" title="${info.ld["genre"]}/${info.ld["name"]} ${name}"><span class="uk-icon-link uk-invisible-hover editor-closer" uk-icon="icon: close; ratio: 0.75"></span><span class="editor-name">${name}</span></a></li>`
      );
      let tabContent = $(
         SafeHTML`<li data-id="${info.id}" data-name="${name}" class="editor-content-tab-item">
            <ul class="uk-iconnav uk-iconnav-vertical editor-content-item-menu">
               <li><a href="#" uk-icon="icon: close" title="Close" class="editor-content-item-close"></a></li>
               <li><a href="#" uk-icon="icon: push" title="Save" class="editor-content-item-save"></a></li>
               <li><a href="#" uk-icon="icon: play" title="Preview" class="editor-content-item-preview"></a></li>
            </ul>
            <div class="editor-content-item ">
               <div class="uk-card uk-card-default uk-card-body editor-part-editor">
               </div>
            </div>
         </li>`
      );
      let tabIndex = $("#editor-content-tabs li").length;
      $("#editor-content-tabs").append(tab);
      $("#editor-content").append(tabContent);
      tab.find(".editor-closer").click(() => {
         tab.remove();
         tabContent.remove();
         setTimeout(
            () => {
               UIkit.switcher("#editor-content-tabs")[0].show(tabIndex-1);
            },
            50
         );
      });
      tabContent.find(".editor-content-item-close").click(() => {
         tab.remove();
         tabContent.remove();
         setTimeout(
            () => {
               UIkit.switcher("#editor-content-tabs")[0].show(tabIndex-1);
            },
            50
         );
      });


      let initializing = true;
      let needsSave = false;
      let source = null;
      let preview = null;
      let markNeedsSaved = () => {
         needsSave = true;
         tab.find(".editor-name").text(name+" *")
      }
      tabContent.find(".editor-content-item-preview").click(() => {
         let content = $(tabContent.find(".editor-part-tabs li")[0]).hasClass("uk-active") ?
            $(source).val() :
            preview.innerHTML;
         if (content.trim().substring(0,9)!="<!DOCTYPE") {
            content = `<!DOCTYPE html>
            <html>
            <head>
            <base href="/data/content/${info.id}/">
            <title>${name}</title>
            ${this.config['preview-wrap-header']!=undefined ? this.config['preview-wrap-header'] : this.config['wrap-header']}
            </head>
            <body>
            ${this.config['wrap-body']!=undefined ? this.config['wrap-body'][0] : ''}
            ${content}
            ${this.config['wrap-body']!=undefined ? this.config['wrap-body'][1] : ''}
            </body>
            </html>
            `
         }
         let previewWindow = window.open("", name);
         previewWindow.document.write(content);

      });
      if (baseContentType=="text/html") {
         tabContent.find(".editor-part-editor").append(SafeHTML`
            <ul uk-tab class="editor-part-tabs">
               <li class="uk-active">
                  <a href="#">Source</a>
               </li>
               <li>
                  <a href="#">Author</a>
               </li>
            </ul>
            <ul class="uk-switcher uk-margin editor-part-panes">
            <li>
               <ul class="uk-iconnav uk-width-1-1 editor-part-editor-source-toolbar uk-margin-bottom">
               <li><button class="uk-button uk-button-default uk-button-small" data-action="wrap" title="Wrap document (add DOCTYPE)" uk-tooltip><span uk-icon="icon: shrink"></span></button></li>
               <li><button class="uk-button uk-button-default uk-button-small" data-action="unwrap" title="Unwrap document (remove DOCTYPE)" uk-tooltip><span uk-icon="icon: expand"></span></button></li>
               <li><button class="uk-button uk-button-default uk-button-small" data-action="article" title="Make article" uk-tooltip>Article</button></li>
               </ul>
               <textarea class="uk-textarea editor-part-editor-source" rows="15" placeholder="Loading ..."></textarea>
            </li>
            <li>
               <iframe class="uk-width-1-1 editor-part-editor-iframe" src="/assets/content/editor.html">
               </iframe>
            </li>
            </ul>`
         )

         tabContent.find(".editor-part-editor-source-toolbar button").on("click",(e) => {
            let action = e.currentTarget.dataset.action;
            //console.log(action);
            if (action=="check") {
               let parser = new DOMParser();
               let doc = parser.parseFromString($(source).val(), "text/html");
               console.log(doc);
            } else if (action=="wrap") {
               if ($(source).val().indexOf("<!DOCTYPE")>=0) {
                  return;
               }
               $(source).text(
`<!DOCTYPE html>
<html>
<head>
<title></title>
${this.config['wrap-header']}
</head>
<body>
${this.config['wrap-body']!=undefined ? this.config['wrap-body'][0] : ''}
${$(source).val()}
${this.config['wrap-body']!=undefined ? this.config['wrap-body'][1] : ''}
</body>
</html>
`
               );
               markNeedsSaved()
            } else if (action=="unwrap") {
               let parser = new DOMParser();
               let doc = parser.parseFromString($(source).val(), "text/html");
               if (doc.documentElement.tagName!='HTML') {
                  return;
               }
               $(source).text($(doc).find("body").html());
               markNeedsSaved()
            } else if (action=="article") {
               let parser = new DOMParser();
               let doc = parser.parseFromString($(source).val(), "text/html");
               if (doc.documentElement.tagName=='ARTICLE') {
                  return;
               } else if (doc.documentElement.tagName=='HTML') {
                  let main = $(doc).find("body > main");
                  let body = $(doc).find("body");
                  let markup = main.length>0 ? main.html().trim() : body.html().trim();
                  if (markup.indexOf("<article>")==0 || markup.indexOf("<article ")==0) {
                     $(source).text(markup);
                  } else {
                     $(source).text(`<article>${markup}</article>`);
                  }
                  markNeedsSaved()
               } else {
                  $(source).val(`<article>${$(source).val()}</article>`);
                  markNeedsSaved()
               }
            }
         });
         // TODO: this timeout is a hack!  ready(iframe.contentDocument) didn't work
         let setupEditor = () => {
            let iframe = tabContent.find(".editor-part-editor-iframe")[0];
            //console.log(iframe);
            $($(iframe.contentDocument).find("head")[0]).append(SafeHTML`<base href="/data/content/${info.id}/">`)
            let body = $(iframe.contentDocument).find("main")[0];
            if (body==undefined) {
               setTimeout(setupEditor,250);
               return;
            }
            $(body).append(SafeHTML`
               <ul class="uk-iconnav uk-width-1-1 editor-part-editor-toolbar">
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="bold" title="bold content" uk-tooltip><span uk-icon="icon: bold"></span></button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="italic" title="italic content" uk-tooltip><span uk-icon="icon: italic"></span></button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="createlink" data-prompt="URL?" title="create link" uk-tooltip><span uk-icon="icon: link" data-action="link"></span></button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="insertunorderedlist" title="insert bulleted list" uk-tooltip><span uk-icon="icon: list"></span></button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="insertorderedlist" title="insert numbered list" uk-tooltip><span uk-icon="icon: hashtag"></span><span uk-icon="icon: list"></span></button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<p>" title="insert paragraph" uk-tooltip>p</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<h1>" title="insert heading, level 1" uk-tooltip>h1</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<h2>" title="insert heading, level 2" uk-tooltip>h2</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<h3>" title="insert heading, level 3" uk-tooltip>h3</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<h4>" title="insert heading, level 4" uk-tooltip>h4</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<h5>" title="insert heading, level 5" uk-tooltip>h5</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<section>" title="insert section" uk-tooltip>section</button></li>
                   <li><button class="uk-button uk-button-default uk-button-small" data-action="formatBlock;<div>" title="insert div" uk-tooltip>div</button></li>
               </ul>
               <div class="editor-part-editor-preview uk-width-1-1" contenteditable="true"></div>
            `);
            preview = $(body).find(".editor-part-editor-preview")[0];
            preview.addEventListener("input",() => {
               markNeedsSaved()
            }, false);
            $(body).find(".editor-part-editor-toolbar a").on("click",(e) => {
               let action = e.currentTarget.dataset.action;
               let range = iframe.contentDocument.getSelection().getRangeAt(0);
               iframe.contentDocument.execCommand(action,false,null);
               markNeedsSaved()
               return false;
            });
            $(body).find(".editor-part-editor-toolbar button").on("click",(e) => {
               let action = e.currentTarget.dataset.action;
               let pos = action.indexOf(";");
               let command = pos<0 ? action : action.substring(0,pos);
               let value = pos<0 ? null : action.substring(pos+1);

               let edit = () => {
                  if (command=="createlink") {
                     let link = iframe.contentDocument.createElement("a");
                     link.setAttribute("href",value);
                     iframe.contentDocument.getSelection().getRangeAt(0).surroundContents(link);
                  } else if (command=="surround") {
                     console.log(value);
                     let container = iframe.contentDocument.createElement(value);
                     iframe.contentDocument.getSelection().getRangeAt(0).surroundContents(container);
                  } else {
                     let range = iframe.contentDocument.getSelection().getRangeAt(0);
                     iframe.contentDocument.execCommand(command,false,value);
                  }
                  markNeedsSaved()
               }
               if (e.currentTarget.dataset.prompt!=undefined) {
                  UIkit.modal.prompt(e.currentTarget.dataset.prompt,"").then((url) => {
                     value = url;
                     edit();
                  });
               } else {
                  edit();
               }
               return false;
            });

         };
         setTimeout(setupEditor,250);

         tabContent.find(".editor-part-panes").on("show", (e,tab) => {
            if (initializing) return;
            //console.log(tab);
            //console.log(tab.toggles);
            if ($(tab.toggles[0]).hasClass("uk-active")) {
               // switched to source
               //console.log(preview.innerHTML);
               //console.log(source);
               $(source).text(preview.innerHTML);
            } else {
               // switch to preview
               preview.innerHTML = $(source).val();
            }
         });

      } else {
         tabContent.find(".editor-part-editor").append(SafeHTML`
            <textarea class="uk-textarea editor-part-editor-source" rows="15" placeholder="Loading ..."></textarea>`
         )
      }
      source = tabContent.find(".editor-part-editor-source")[0];
      source.addEventListener("input",() => {
         needsSave = true;
         tab.find(".editor-name").text(name+" *")
      }, false);
      tabContent.find(".editor-content-item-save").click(() => {
         console.log(`Save content part ${info.id} ${name}`);
         let content = $(tabContent.find(".editor-part-tabs li")[0]).hasClass("uk-active") ?
            $(source).val() :
            preview.innerHTML;
         if (creating) {
            this.client.createContentResource(info.id,name,"hasPart",contentType,content)
               .then((obj) => {
                  UIkit.notification("<span uk-icon='icon: check'></span> Content part created.");
                  if (onUpdate) {
                     onUpdate(name,contentType,creating);
                  }
                  if (info.ld.hasPart==undefined) {
                     info.ld.hasPart = []
                  }
                  console.log(obj)
                  info.ld.hasPart.push(obj)
                  creating = false
                  tab.find(".editor-name").text(name)
               })
               .catch((status) => {
                  if (status==401) {
                     console.log("Login expired...");
                     this.login();
                  } else {
                     this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
                  }
               });
         } else {
            this.client.updateContentResource(info.id,name,contentType,content)
               .then(() => {
                  UIkit.notification("<span uk-icon='icon: check'></span> Content part saved.");
                  tab.find(".editor-name").text(name)
                  if (onUpdate) {
                     onUpdate(name,contentType,creating);
                  }
               })
               .catch((status) => {
                  if (status==401) {
                     console.log("Login expired...");
                     this.login();
                  } else {
                     this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
                  }
               });
         }
      });
      setTimeout(
         () => {
            UIkit.switcher("#editor-content-tabs")[0].show(tabIndex);
         },
         50
      );
      if (creating) {
         tab.find(".editor-name").text(name+" *")
         if (baseContentType=="text/html") {
            $(source).text("<article><p>Your text goes here...</p></article>");
         } else if (baseContentType=="text/markdown") {
            $(source).text("# Title");
         }
         contentType = baseContentType + "; charset=UTF-8";
      } else {
         let tryLoadContent = () => {
            this.client.getContentResource(info.id,name)
               .then((text) => {
                  initializing = false;
                  $(source).text(text);
                  if (preview!=undefined) {
                     $(preview).append(text);
                  }
               })
               .catch((status) => {
                  if (status==401) {
                     console.log("Login expired...");
                     this.login(tryLoadContent);
                  } else {
                     this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
                  }
               });
         };
         tryLoadContent();
      }

   }

   deleteContent(row,dataset) {
      UIkit.modal.confirm(`Are you sure you want to delete ${dataset["genre"]}/${dataset["name"]}?`)
         .then(
            () => {
               console.log("Delete content");
               let id = this.contentIdFromURL(dataset.url);
               if (!id) {
                  this.error(`Cannot parse content URI ${dataset.url}`);
                  return;
               }
               console.log(`Deleting ${id}`);
               let table = row.parentNode;
               var cleanup = function() {
                  let count = 0;
                  $(table).find("tr").each((i,row) => {
                     count++;
                  });
                  if (count<=1) {
                     $(table.parentNode.parentNode.parentNode).remove();
                  }
               };
               this.client.deleteContent(id)
                  .then(() => {
                     console.log("Success!");
                     $(row).remove();
                     cleanup();
                     UIkit.notification(`<span uk-icon='icon: check'></span> Deleted ${dataset["genre"]}/${dataset["name"]}`);
                  })
                  .catch((status) => {
                     if (status==401) {
                        console.log("Login expired...");
                        this.login();
                     } else if (status==404) {
                        $(row).remove();
                        cleanup();
                     } else {
                        this.error(`Cannot delete content ${idMatch[1]}, status ${status}`);
                     }
                  });
         })
   }

   deleteContentMediaResource(item,info,name) {
      UIkit.modal.confirm(`Are you sure you want to delete media ${name}?`)
         .then(
            () => {
               console.log(`Deleting media ${info.id} ${name}`);
               this.client.deleteContentResource(info.id,name)
                  .then(() => {
                     console.log("Success!");
                     $(item).remove();
                     UIkit.notification(`<span uk-icon='icon: check'></span> Deleted media ${name}`);
                     for (let i in info.ld.associatedMedia) {
                        if (info.ld.associatedMedia[i].name==name) {
                           info.ld.associatedMedia.splice(i)
                           break;
                        }
                     }
                     if (info.ld.associatedMedia.length==0) {
                        delete info.ld["associatedMedia"];
                     }
                     console.log(info.ld);
                  })
                  .catch((status) => {
                     if (status==401) {
                        console.log("Login expired...");
                        this.login();
                     } else if (status==404) {
                        $(item).remove();
                     } else {
                        this.error(`Cannot delete resource ${name}, status ${status}`);
                     }
                  });
         })
   }
   deleteContentPart(item,info,name) {
      UIkit.modal.confirm(`Are you sure you want to delete part ${name}?`)
         .then(
            () => {
               console.log(`Deleting part ${info.id} ${name}`);
               this.client.deleteContentResource(info.id,name)
                  .then(() => {
                     console.log("Success!");
                     $(item).remove();
                     UIkit.notification(`<span uk-icon='icon: check'></span> Deleted part ${name}`);
                     // Check to see if it is already open.  If so, switch to that tab.
                     $("#editor-content-tabs li").each((i,tab) => {
                        if (tab.dataset.id==info.id && tab.dataset.name==name) {
                           $(tab).remove();
                        }
                     });
                     $("#editor-content li").each((i,tab) => {
                        if (tab.dataset.id==info.id && tab.dataset.name==name) {
                           $(tab).remove();
                        }
                     });
                     for (let i in info.ld.hasPart) {
                        if (info.ld.hasPart[i].name==name) {
                           info.ld.hasPart.splice(i)
                           break;
                        }
                     }
                     if (info.ld.hasPart.length==0) {
                        delete info.ld["hasPart"];
                     }
                     console.log(info.ld);
                  })
                  .catch((status) => {
                     if (status==401) {
                        console.log("Login expired...");
                        this.login();
                     } else if (status==404) {
                        $(item).remove();
                     } else {
                        this.error(`Cannot delete resource ${name}, status ${status}`);
                     }
                  });
         })
   }

}

class DuckpondClient {
   constructor(service) {
      this.service = service;
   }

   getContents() {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/",{credentials: 'include'}).then(
            (response) => {
               if (response.ok) {
                  response.json().then((data) => {
                     resolve(data)
                  });
               } else {
                  reject(response.status);
               }
            }
         );
      });
   }

   createContent(typeName,genre,name,headline) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/",{
             method: 'post',
             credentials: 'include',
             headers: {
               "Content-type": "application/ld+json; charset=UTF-8"
             },
             body: JSON.stringify({
                "@context" : "http://schema.org/",
                "@type" : typeName,
                "genre" : genre,
                "name" : name,
                "headline" : headline
             })
          }).then(
             (response) => {
                if (response.ok) {
                   let value = {
                     'location' : response.headers.get('location'),
                     'modified' : response.headers.get('date-modified')
                   };
                   resolve(value);
                } else {
                   reject(response.status);
                }
             }
          )

      });
   }


   deleteContent(id) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/",{
             method: 'delete',
             credentials: 'include'
          }).then(
             (response) => {
                if (response.ok) {
                   resolve();
                } else {
                   reject(response.status);
                }
             }
          )

      });
   }

   getContent(id) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/",{credentials: 'include'}).then(
            (response) => {
               if (response.ok) {
                  response.json().then((data) => {
                     resolve(data)
                  });
               } else {
                  reject(response.status);
               }
            }
         );
      });
   }

   updateContent(id,ld) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/",{
             method: 'put',
             credentials: 'include',
             headers: {
               "Content-type": "application/ld+json; charset=UTF-8"
             },
             body: JSON.stringify(ld)
          }).then(
             (response) => {
                if (response.ok) {
                   response.json().then((data) => {
                      resolve(data)
                   });
                } else {
                   reject(response.status);
                }
             }
          )

      });
   }

   getContentResource(id,resource) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/" + resource,{credentials: 'include'}).then(
            (response) => {
               if (response.ok) {
                  response.text().then((data) => {
                     resolve(data)
                  });
               } else {
                  reject(response.status);
               }
            }
         );
      });
   }

   createContentResource(id,resource,property,contentType,data) {
      let headers = new Headers();
      headers.append('Content-Type',contentType);
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/" + resource + ";" + property,{
            method : 'put',
            credentials: 'include',
            headers : headers,
            body: data
         }).then(
            (response) => {
               if (response.ok) {
                  response.json().then((data) => {
                     resolve(data)
                  });
               } else {
                  reject(response.status);
               }
            }
         );
      });
   }
   updateContentResource(id,resource,contentType,data) {
      let headers = new Headers();
      headers.append('Content-Type',contentType);
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/" + resource,{
            method : 'put',
            credentials: 'include',
            headers : headers,
            body: data
         }).then(
            (response) => {
               if (response.ok) {
                  resolve()
               } else {
                  reject(response.status);
               }
            }
         );
      });
   }
   deleteContentResource(id,name) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/" + name,{
             method: 'delete',
             credentials: 'include'
          }).then(
             (response) => {
                if (response.ok) {
                   resolve();
                } else {
                   reject(response.status);
                }
             }
          )

      });
   }

}

var editor = new DuckpondEditor(new DuckpondClient("/data/"));

$(document).ready(function() {
   editor.bind();
   editor.reloadContents();
})
