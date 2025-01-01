CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE users (
    id SERIAL PRIMARY KEY,                 -- ID tự động tăng
    useridpos VARCHAR(255),       -- ID người dùng (có thể là mã duy nhất)
    imagepath TEXT,               -- Đường dẫn đến ảnh
    imgbedding VECTOR(512)        -- Vector ảnh (sử dụng pgvector với kích thước 512)
);

