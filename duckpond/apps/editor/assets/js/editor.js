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
         SafeHTML`<li data-url="${dataset.url}">
            <ul class="uk-iconnav uk-iconnav-vertical editor-content-item-menu">
               <li><a href="#" uk-icon="icon: close" title="Close" class="editor-content-item-close"></a></li>
               <li><a href="#" uk-icon="icon: refresh" title="Refresh" class="editor-content-item-refresh"></a></li>
               <li><a href="#" uk-icon="icon: push" title="Save" class="editor-content-item-save"></a></li>
            </ul>
            <div class="editor-content-item">
               <p>Loading ...</p>
            </div>
         </li>`
      );
      let tab = $(
         SafeHTML`<li data-url="${dataset.url}"><a href="#" title="${dataset.headline}">${dataset.genre} / ${dataset.name}</a></li>`
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
         })
         .catch((status) => {
            this.error(`Cannot retrieve content ${idMatch[1]}, status ${status}`);
         })
   }

   deleteContent(row,dataset) {
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


}

var editor = new DuckpondEditor(new DuckpondClient("/data/"));

$(document).ready(function() {
   editor.bind();
   editor.reloadContents()
})
