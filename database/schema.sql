create table stock_sessions
(
    chat_id int not null
        constraint stock_sessions_pk
            primary key,
    title TEXT,
    hashtags TEXT,
    price REAL,
    description TEXT,
    step TEXT not null
);

create table images
(
    image_path TEXT
        constraint images_pk
            primary key,
    chat_id int not null
        references stock_sessions
);

