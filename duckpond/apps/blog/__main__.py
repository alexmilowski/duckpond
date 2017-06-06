
from duckpond.apps.blog.app import app
from duckpond.apps.blog.assets import assets
from duckpond.apps.blog.docs import docs
from duckpond.apps.blog.views import views
app.register_blueprint(assets)
app.register_blueprint(docs)
app.register_blueprint(views)

if __name__ == '__main__':
    app.run()
