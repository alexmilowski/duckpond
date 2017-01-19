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
               this.createContent(genre.value.trim(),name.value.trim(),typeSelect.value=="Custom" ? typeCustom.value.trim() : typeSelect.value,title.value.trim());
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
               this.deleteContent($(e.currentTarget).closest("tr").get(0).dataset);
            }
         );
         console.log("Finished.")
      }).catch((status) => {
         console.log("Cannot load content, status "+status);
      })
   }

   editContent(dataset) {
      console.log("Edit content");
      console.log(dataset);
   }

   deleteContent(dataset) {
      console.log("Delete content");
      console.log(dataset);
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

   createContent() {
   }

   deleteContent(dataset) {
   }

}

var editor = new DuckpondEditor(new DuckpondClient("/data/"));

$(document).ready(function() {
   editor.bind();
   editor.reloadContents()
})
