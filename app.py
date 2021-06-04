from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask.helpers import url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required
import os

UPLOAD_FOLDER = "./static/img/"
ALLOWED_EXTENSIONS = {'.jpg', '.png'}

app = Flask(__name__)

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Session(app)

db = SQL("sqlite:///blogFlask.db")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        email = request.form.get("email")
        nombre = request.form.get("name")
        apellido = request.form.get("lastname")

        rows = db.execute("select * from usuario where username = :username", username = username)
        if len(rows) != 0:
            return render_template("register.html", error="Usuario ya registrado")
        id_user = db.execute(f"INSERT INTO usuario (username,password,name,lastname,email) VALUES ('{username}','{password}','{nombre}','{apellido}','{email}''')")
        session["id_user"] = id_user
        return redirect("/")
    else:
        return render_template("register.html")

@app.route("/")
@login_required
def index():
    posts = db.execute("SELECT p.*, u.username FROM post p INNER JOIN usuario u on u.id_user = p.autor")
    comentarios =db.execute("SELECT c.*, u.username FROM comentarios c INNER JOIN usuario u on u.id_user = c.id_user")
    print(comentarios)
    print(posts)
    return render_template("index.html", posts = posts, comentarios=comentarios)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        rows = db.execute("select * from usuario where username = :username", username = username)
        if len(rows) == 0:
            return render_template("login.html", error="Usuario no existe")
        password_db = rows[0]["password"]
        if not check_password_hash(password_db, password):
            return render_template("login.html", error="contraseña incorrecta")
        else:
            session["id_user"] = rows[0]["id_user"]
            return redirect("/")
    else:
        return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect("/")

@app.route("/editarperfil")
@login_required
def editarperfil():
    if request.method == "POST":
        if "archivo" not in request.files:
            return redirect("/editarperfil")
        
        archivo = request.files['archivo']

        if archivo.filename == "":
            return redirect("/editarperfil")

        if archivo:
            nombreArchivo = archivo.filename
            archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombreArchivo))
           
            #(f"INSERT INTO usuario (username,password,name,lastname,email) VALUES ('{username}','{password}','{nombre}','{apellido}','{email}''')")
            db.execute(f"update post (autor, descripcion, photo) VALUES (:id_user, :texto, :urlimg)",
                   id_user=session["id_user"],
                   texto = request.form.get("texto"),
                   urlimg = os.path.join(app.config["UPLOAD_FOLDER"], nombreArchivo) )
            return redirect("/perfil")
        else:
            return redirect("/editarperfil")
    else:

        return redirect("/perfil")

@app.route("/perfil")
@login_required
def perfil():
    image_file = url_for('static', filename='img/')
    return render_template("account.html", image_file=image_file)

@app.route("/agregarpost")
@login_required
def agregarpost():
    
    return render_template("agregarpost.html")

@app.route("/crear", methods=["GET", "POST"])
@login_required
def crearpost():
    if request.method == "POST":
        if "archivo" not in request.files:
            return redirect("/agregarpost")
        
        archivo = request.files['archivo']

        if archivo.filename == "":
            return redirect("/agregarpost")

        if archivo:
            nombreArchivo = archivo.filename
            archivo.save(os.path.join(app.config["UPLOAD_FOLDER"], nombreArchivo))
           
            #(f"INSERT INTO usuario (username,password,name,lastname,email) VALUES ('{username}','{password}','{nombre}','{apellido}','{email}''')")
            db.execute(f"INSERT INTO post (autor, descripcion, photo) VALUES (:id_user, :texto, :urlimg)",
                   id_user=session["id_user"],
                   texto = request.form.get("texto"),
                   urlimg = (os.path.join(app.config["UPLOAD_FOLDER"], nombreArchivo))[1:len(os.path.join(app.config["UPLOAD_FOLDER"], nombreArchivo))] )
            return redirect("/")
        else:
            return redirect("/agregarpost")
    else:
        return redirect("/")

@app.route("/post")
@login_required
def post():
    posts = db.execute("SELECT p.*, u.username FROM post p INNER JOIN usuario u on u.id_user = p.autor WHERE id_user = :id_user group by id_post", id_user=session["id_user"])
    print(posts)
    return render_template("post.html", posts=posts)

@app.route("/post/<post_id>")
@login_required
def postver(post_id):
    posts = db.execute("SELECT p.*, u.username FROM post p INNER JOIN usuario u on u.id_user = p.autor WHERE id_post = :post_id", post_id=post_id)
    
    comentarios = db.execute("SELECT c.*, u.username FROM comentario c INNER JOIN usuario u on u.id_user = c.id_user WHERE id_post = :post_id", post_id=post_id)

    return render_template("post.html", posts=posts, comentarios=comentarios)

@app.route("/editarpost/<post_id>", methods=["POST", "GET"])
@login_required
def editarpost(post_id):
    posts = db.execute("SELECT p.*, u.username FROM post p INNER JOIN usuario u on u.id_user = p.autor WHERE id_post = :post_id", post_id=post_id)
    
    if not posts:
        return render_template("editarpost.html", error="No se encontro post")

#Que el edit y delete sea desde el perfil

    if request.method == "POST":
        #id_post = request.form.get("id_post")
        descripcion = request.form.get("texto")
        db.execute(f"UPDATE post SET descripcion={descripcion} WHERE id_post={post_id}")
        return redirect(f"/perfil")
    #return redirect("/")
    return render_template("editarpost.html", posts=posts)



@app.route("/eliminarpost/<post_id>", methods=["POST", "GET"])
def eliminar(post_id):
    posts = db.execute("SELECT p.*, u.username FROM post p INNER JOIN usuario u on u.id_user = p.autor WHERE id_post = :post_id", post_id=post_id)
    
    if not posts:
        return render_template("perfil.html", error="No se encontro post")

#Que el edit y delete sea desde el perfil
    db.execute("Delete from post where id_post={post_id}")
    return redirect(f"/perfil")
    #return redirect("/")
    #return render_template("editarpost.html", posts=posts)

'''@app.route("/buscar")
@login_required
def buscar():
    buscar = db.execute("SELECT username FROM usuario WHERE id_user = :id_user", id_user=session["id_user"])
    print(buscar)
    return render_template("perfil.html", buscar=buscar)'''

@app.route("/buscarpost", methods=["POST"] )
@login_required
def buscarpost():
    k = request.args.get("buscar")
    buscar = db.execute("SELECT p.*, u.username FROM post p INNER JOIN usuario u on u.id_user = p.autor  WHERE descripcion like '%:k%'", k=k)
    print(buscar)
    return render_template("index.html", posts=buscar)

@app.route("/agregarcomentario", methods=["POST"] )
@login_required
def agregarcomentario():
    if request.method == "POST":
        id_post = request.form.get("id_post")
        comentario = request.form.get("comentario")
        #Verificar si asi se llaman los campos de la tabla
        db.execute(f"INSERT INTO comentario (id_post, id_user, descripcion) VALUES (:id_post, :id_user, :comentarios)", 
                    id_user=session["id_user"], id_post=id_post, comentario=comentario)
        
        return redirect(f"/post/{id_post}")
    else:
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True, port=8000)