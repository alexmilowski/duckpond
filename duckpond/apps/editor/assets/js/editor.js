class DuckpondEditor {
   constructor() {

   }

   init() {
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
   }

   createContent() {
      console.log("Add content");
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

var app = new DuckpondEditor();

$(document).ready(function() {
   app.init();
})
