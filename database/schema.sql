create table stock_sessions
(
	chat_id int not null
		constraint stock_sessions_pk
			primary key,
	title TEXT,
	hashtags TEXT,
	price REAL,
	description TEXT,
	images BLOB,
	step TEXT
);

create unique index stock_sessions_chat_id_uindex
	on stock_sessions (chat_id);

