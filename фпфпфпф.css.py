* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background-color: #f8f9fa;
    color: #333;
    line-height: 1.6;
}

/* Header */
header {
    background-color: white;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    padding: 15px 20px;
}

nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

nav ul {
    display: flex;
    list-style: none;
}

nav li a {
    padding: 8px 15px;
    text-decoration: none;
    color: #333;
    border: 1px solid #ddd;
    border-radius: 4px;
    margin-right: 10px;
    transition: background-color 0.3s;
}

nav li a:hover {
    background-color: #e9ecef;
}

.header-actions button {
    margin-left: 10px;
    padding: 8px 15px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}

.btn-outline {
    background-color: white;
    color: #0d6efd;
    border: 2px solid #0d6efd;
}

.btn-outline:hover {
    background-color: #0d6efd;
    color: white;
}

.btn-primary {
    background-color: #0d6efd;
    color: white;
}

.btn-primary:hover {
    background-color: #0b5ed7;
}

/* Hero Section */
.hero {
    display: flex;
    align-items: center;
    padding: 60px 80px;
    background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
    gap: 40px;
}

.hero-content h1 {
    font-size: 2.5rem;
    margin-bottom: 15px;
    line-height: 1.3;
}

.hero-content p {
    color: #6c757d;
    margin-bottom: 20px;
    font-size: 0.9rem;
}

.hero-buttons {
    display: flex;
    gap: 15px;
    margin-top: 20px;
}

.btn-video {
    display: flex;
    align-items: center;
    gap: 8px;
    background: none;
    border: 1px solid #0d6efd;
    color: #0d6efd;
    padding: 10px 20px;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
}

.btn-video span {
    font-size: 1.2rem;
}

.btn-yellow {
    background-color: #ffc107;
    color: #212529;
    border: none;
    padding: 10px 20px;
    border-radius: 20px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s;
}

.btn-yellow:hover {
    background-color: #e0a800;
}

.hero-image img {
    max-width: 100%;
    height: auto;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

/* Video Instruction */
.video-instruction {
    padding: 60px 80px;
    text-align: center;
}

.video-instruction h2 {
    font-size: 2rem;
    margin-bottom: 30px;
}

.video-card {
    position: relative;
    width: 100%;
    max-width: 600px;
    margin: 0 auto;
    border-radius: 15px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.video-card img {
    width: 100%;
    height: auto;
    display: block;
}

.video-overlay {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: rgba(255,255,255,0.8);
    padding: 20px;
    border-radius: 50%;
    cursor: pointer;
}

.video-overlay span {
    font-size: 2rem;
    font-weight: bold;
    color: #0d6efd;
}

.video-card p {
    padding: 15px;
    background-color: #f8f9fa;
    font-weight: bold;
    margin: 0;
}

/* How It Works */
.how-it-works {
    padding: 60px 80px;
    text-align: center;
}

.how-it-works h2 {
    font-size: 2rem;
    margin-bottom: 40px;
}

.steps {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 30px;
}

.step {
    width: 200px;
    padding: 20px;
    background-color: white;
    border-radius: 10px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    text-align: center;
}

.step img {
    width: 100%;
    height: 100px;
    object-fit: cover;
    border-radius: 8px;
    margin-bottom: 15px;
}

.step h3 {
    margin-bottom: 10px;
    font-size: 1.1rem;
}

.step p {
    font-size: 0.9rem;
    color: #6c757d;
}

/* FAQ Section */
.faq {
    padding: 60px 80px;
    text-align: center;
    background-color: #f8f9fa;
}

.faq h2 {
    font-size: 2rem;
    margin-bottom: 15px;
}

.faq p {
    color: #6c757d;
    margin-bottom: 30px;
    font-size: 1rem;
}

.faq-buttons {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
}

/* Footer */
footer {
    text-align: center;
    padding: 20px;
    background-color: #343a40;
    color: white;
    font-size: 0.9rem;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero {
        flex-direction: column;
        padding: 40px 20px;
    }

    .hero-content h1 {
        font-size: 2rem;
    }

    .video-instruction,
    .how-it-works,
    .faq {
        padding: 40px 20px;
    }

    .steps {
        flex-direction: column;
        align-items: center;
    }

    .step {
        width: 100%;
        max-width: 300px;
    }
}