
from duckpond.apps.blog.app import app
from duckpond.apps.blog.views import blog,assets,docs
app.register_blueprint(assets)
app.register_blueprint(docs)
app.register_blueprint(views)

if __name__ == '__main__':
    app.run()
