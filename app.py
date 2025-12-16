from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# =====================================================
# Load environment variables
# =====================================================
load_dotenv()

# =====================================================
# Flask App
# =====================================================
app = Flask(__name__)

# =====================================================
# CORS Configuration
# =====================================================
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    }
)

# =====================================================
# Database Configuration
# =====================================================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in environment variables")

def get_db_connection():
    """Create a PostgreSQL database connection"""
    return psycopg2.connect(DATABASE_URL)

# =====================================================
# Initialize Database
# =====================================================
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database initialized")

    except Exception as e:
        print("❌ Database initialization failed:", e)
        raise

# =====================================================
# Routes
# =====================================================

@app.route("/")
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Blog API is running",
        "endpoints": {
            "GET /api/posts": "Get all posts",
            "POST /api/posts": "Create new post",
            "PUT /api/posts/<id>": "Update post",
            "DELETE /api/posts/<id>": "Delete post"
        }
    })

# -------------------------------
# GET ALL POSTS
# -------------------------------
@app.route("/api/posts", methods=["GET"])
def get_posts():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM posts ORDER BY created_at DESC")
        posts = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify(posts), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# CREATE POST
# -------------------------------
@app.route("/api/posts", methods=["POST"])
def create_post():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400

        if len(title) > 200:
            return jsonify({"error": "Title must be <= 200 characters"}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            INSERT INTO posts (title, content)
            VALUES (%s, %s)
            RETURNING *
            """,
            (title, content)
        )

        new_post = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        return jsonify(new_post), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# UPDATE POST
# -------------------------------
@app.route("/api/posts/<int:id>", methods=["PUT"])
def update_post(id):
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        title = data.get("title", "").strip()
        content = data.get("content", "").strip()

        if not title or not content:
            return jsonify({"error": "Title and content are required"}), 400

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute(
            """
            UPDATE posts
            SET title = %s, content = %s
            WHERE id = %s
            RETURNING *
            """,
            (title, content, id)
        )

        updated_post = cur.fetchone()

        if not updated_post:
            cur.close()
            conn.close()
            return jsonify({"error": "Post not found"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify(updated_post), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# DELETE POST
# -------------------------------
@app.route("/api/posts/<int:id>", methods=["DELETE"])
def delete_post(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM posts WHERE id = %s RETURNING id",
            (id,)
        )

        deleted = cur.fetchone()

        if not deleted:
            cur.close()
            conn.close()
            return jsonify({"error": "Post not found"}), 404

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"message": "Post deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =====================================================
# App Entry Point
# =====================================================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
