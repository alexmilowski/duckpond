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

   reloadContents() {
      this.client.getContents().then((contents) => {
         console.log("Refreshing content display...")
         $("#editor-contents .content-row").remove();
         for (let content of contents) {
            $("#editor-contents").append(
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
         console.log("Cannot load content, status "+status);
      })
   }

   createContent(typeName,genre,name,title) {
      this.client.createContent(typeName,genre,name,title)
         .then((location) => {
            console.log(location)
            let row = $(
               `<tr class="content-row"
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
            $("#editor-contents").append(row)
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
         })
         .catch((status) => {
            console.log(`Cannot create content, status ${status}`)
         });

   }

   editContent(dataset) {
      console.log("Edit content");
      console.log(dataset);
   }

   deleteContent(row,dataset) {
      console.log("Delete content");
      let idMatch = dataset.url.match(/\/([^\/]+)\/$/);
      if (idMatch) {
         console.log(`Deleting ${idMatch[1]}`);
         this.client.deleteContent(idMatch[1])
            .then(() => {
               console.log("Success!");
               $(row).remove();
            })
            .catch((status) => {
               console.log(`Cannot delete content ${idMatch[1]}, status ${status}`);
            })
      } else {
         console.log(`Cannot parse content URI ${dataset.url}`);
      }
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

}

var editor = new DuckpondEditor(new DuckpondClient("/data/"));

$(document).ready(function() {
   editor.bind();
   editor.reloadContents()
})
