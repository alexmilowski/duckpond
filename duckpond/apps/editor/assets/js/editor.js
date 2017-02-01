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
      $("#editor-create-content").click(
         (e) => {
            let genre = $("#editor-form-content-create").find("input[name=genre]").get(0);
            let name = $("#editor-form-content-create").find("input[name=name]").get(0);
            let typeSelect = $("#editor-form-content-create").find("select[name=type-select]").get(0);
            let typeCustom = $("#editor-form-content-create").find("input[name=type-custom]").get(0);
            let title = $("#editor-form-content-create").find("input[name=title]").get(0);
            let valid = true;
            if (genre.value.trim()=="") {
               $(genre).addClass("uk-form-danger")
               valid = false;
            } else {
               $(genre).removeClass("uk-form-danger")
            }
            if (name.value.trim()=="") {
               $(name).addClass("uk-form-danger")
               valid = false;
            } else {
               $(name).removeClass("uk-form-danger")
            }
            if (title.value.trim()=="") {
               $(title).addClass("uk-form-danger")
               valid = false;
            } else {
               $(title).removeClass("uk-form-danger")
            }
            if (typeSelect.value=="Custom" && typeCustom.value.trim()=="") {
               $(typeCustom).addClass("uk-form-danger")
               valid = false;
            } else {
               $(typeCustom).removeClass("uk-form-danger")
            }
            if (valid) {
               this.createContent(typeSelect.value=="Custom" ? typeCustom.value.trim() : typeSelect.value,genre.value.trim(),name.value.trim(),title.value.trim());
            }
         }
      );
      $(".editor-reload-content").click(
         (e) => {
            this.reloadContents();
         }
      );
   }

   error(message) {
      this.notify("Woah!",message);
   }

   notify(title,message) {
      $("#editor-notify-title").text(title)
      $("#editor-notify-message").text(message)
      UIkit.modal("#editor-notify")[0].toggle()
   }

   reloadContents() {
      this.client.getContents().then((contents) => {
         console.log("Refreshing content display...")
         $("#editor-content-list .content-row").remove();
         for (let content of contents) {
            $("#editor-content-list").append(
               `<tr class="content-row"
                    data-url="${content.url}"
                    data-genre="${content.genre}"
                    data-name="${content.name}"
                    data-type="${content['@type']}"
                    data-headline="${content.headline}">
                <td><a href="#" class="uk-icon-link editor-edit-content" uk-icon="icon: file-edit" title="edit"></a></td>
                <td>${content.genre}</td>
                <td>${content.name}</td>
                <td>${content['@type']}</td>
                <td>${content.headline}</td>
                <td><a href="#" class="uk-icon-link editor-delete-content" uk-icon="icon: trash" title="delete"></a></td>
                </tr>`
            )
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
         this.error(`Cannot load content, status ${status}`);
      })
   }

   createContent(typeName,genre,name,title) {
      this.client.createContent(typeName,genre,name,title)
         .then((location) => {
            console.log(location)
            // Create the row
            let row = $(
               SafeHTML`<tr class="content-row"
                    data-url="${location}"
                    data-genre="${genre}"
                    data-name="${name}"
                    data-type="${typeName}"
                    data-headline="${title}">
                <td><a href="#" class="uk-icon-link editor-edit-content" uk-icon="icon: file-edit" title="edit"></a></td>
                <td>${genre}</td>
                <td>${name}</td>
                <td>${typeName}</td>
                <td>${title}</td>
                <td><a href="#" class="uk-icon-link editor-delete-content" uk-icon="icon: trash" title="delete"></a></td>
                </tr>`
            );
            $("#editor-content-list").append(row)

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
            if (status==409) {
               this.notify("Conflicting Content",`A content item with genre "${genre}" and name "${name}" already exists`);
            } else {
               this.error(`Cannot create content, status ${status}`);
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
      })
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
         SafeHTML`<li data-url="${dataset.url}" class="editor-content-tab"><a href="#" title="${dataset.headline}">${dataset.genre} / ${dataset.name}</a></li>`
      );
      let tabIndex = $("#editor-content-tabs li").length;
      $("#editor-content-tabs").append(tab);
      $("#editor-content").append(tabContent);
      tabContent.find(".editor-content-item-close").click((e) => {
         tab.remove();
         tabContent.remove();
         UIkit.switcher("#editor-content-tabs")[0].show(tabIndex-1);
      });
      tabContent.find(".editor-content-item-refresh").click((e) => {

      });
      tabContent.find(".editor-content-item-save").click((e) => {

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
            console.log(data);
            this.addContentEdit(id,data,tabContent)
         })
         .catch((status) => {
            this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
         })
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
      contentItem.append($(SafeHTML`
         <div class="uk-card uk-card-default uk-card-body">
         <h3><span>${data["@type"]}</span></h3>
         <p>modified ${data["dateModified"]}</p>
         </div>`));
      let properties = $(SafeHTML`
         <div class="uk-card uk-card-default uk-card-body uk-margin">
         <h3 class="uk-heading-line"><span>Properties</span></h3>
         <div></div>
         </div>`);
      contentItem.append(properties);
      let propertiesBody = properties.find("div");
      let partList = [];
      let mediaList = [];
      for (let property of Object.keys(data)) {
         if (property=="@context" || property=="@id" || property=="@type" || property=="dateModified" || property=="url" || property=="author") {
            continue;
         } else if (property=="hasPart"){
            partList = data[property]
         } else if (property=="associatedMedia"){
            mediaList = data[property]
         } else {
            let inputType = this.inputTypeFor(property);
            if (inputType=="textarea") {
               let row = $(SafeHTML`
                  <div class="uk-margin">
                     <label class="uk-form-label" for="${property}" >${property}</label>
                     <div class="uk-form-controls">
                        <textarea class="uk-textarea" name="${property}" cols="40" rows="5">${data[property]}</textarea>
                     </div>
                  </div>`);
               propertiesBody.append(row);
            } else {
               let row = $(SafeHTML`
                  <div class="uk-margin">
                     <label class="uk-form-label" for="${property}" >${property}</label>
                     <div class="uk-form-controls">
                        <input class="uk-input" value="${data[property]}" name="${property}" size="40">
                     </div>
                  </div>`);
               propertiesBody.append(row);
            }
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
             <li><a href="#" uk-icon="icon: plus" title="Add Part" class="editor-content-part-add"></a></li>
             </ul>
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
      footer.find(".editor-content-part-add").click(() => {
         console.log("Add part");
         console.log(info);
         return false;
      })

      let contentPartList = footer.find(".editor-content-parts");
      let addPart = (name,contentType) => {
         let item = $(SafeHTML`
            <li>${name}; ${contentType}
               <a href="#" uk-icon="icon: file-edit" title="Edit Part" class="uk-icon-link editor-content-part-edit"></a>
               <a href="#" uk-icon="icon: download" title="Edit Part" class="uk-icon-link editor-content-part-download"></a>
               <a href="#" uk-icon="icon: trash" title="Delete Part" class="uk-icon-link editor-content-part-delete"></a>
            </li>
         `);
         contentPartList.append(item);
         item.find(".editor-content-part-edit").click(() => {
            console.log(`Edit part ${name}`);
            return false;
         });
         item.find(".editor-content-part-download").click(() => {
            console.log(`Download part ${name}`);
            open(`/data/content/${info.id}/${name}`,name);
            return false;
         });
         item.find(".editor-content-part-delete").click(() => {
            console.log(`Delete part ${name}`);
            console.log(part);
            console.log(info);
            setTimeout(() => {
               UIkit.modal.confirm(`Are you sure you want to delete ${name}?`)
                  .then(
                     () => {
                        console.log(`Deleting ${name} ...`);
                     }
                  )
            },25);
            return false;
         });
      };
      for (let part of partList) {
         addPart(part["name"],part["fileFormat"])
      }
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
            console.log(`Delete media ${name}`);
            setTimeout(() => {
               this.deleteContentMediaResource(item,info.id,name);
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

            let name = arguments[0].responseJSON["name"];
            let existing = false;
            contentMediaList.find("li").each((i,item) => {
               if (item.dataset.name==name) {
                  existing = true;
               }
            });
            if (!existing) {
               addMedia(name,arguments[0].responseJSON["content-type"]);
            }

            setTimeout(function () {
               bar.setAttribute('hidden', 'hidden');
            }, 1000);

            alert('Upload Completed');
         }
      });

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
               this.client.deleteContent(id)
                  .then(() => {
                     console.log("Success!");
                     $(row).remove();
                  })
                  .catch((status) => {
                     if (status==404) {
                        $(row).remove();
                     } else {
                        this.error(`Cannot delete content ${idMatch[1]}, status ${status}`);
                     }
                  });
         })
   }

   deleteContentMediaResource(item,id,name) {
      UIkit.modal.confirm(`Are you sure you want to delete ${name}?`)
         .then(
            () => {
               console.log(`Deleting ${name}`);
               this.client.deleteContentResource(id,name)
                  .then(() => {
                     console.log("Success!");
                     $(item).remove();
                  })
                  .catch((status) => {
                     if (status==404) {
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
         fetch(this.service + "content/").then(
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
                   console.log(response)
                   resolve(response.headers.get('location'));
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
             method: 'delete'
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
         fetch(this.service + "content/" + id + "/").then(
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

   deleteContentResource(id,name) {
      return new Promise((resolve,reject) => {
         fetch(this.service + "content/" + id + "/" + name,{
             method: 'delete'
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
   editor.reloadContents()
})
