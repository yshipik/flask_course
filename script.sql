create table if not exists menu (
    id integer primary key autoincrement not null,
    title text not null,
    url text not null
);

create table if not exists users (
    id integer primary key autoincrement,
    username text not null,
    password text not null,
    register_date date not null,
    is_stuff bool not null
);

create table if not exists stuff (
    id integer primary key autoincrement,
    title text not null,
    description text not null,
    price int not null,
    creation_date date not null,
    picture text not null
);

create table if not exists orders (
    id int primary key,
    timestamp date,
    state text not null,
    location text not null
);

create table if not exists purchases (
    id integer primary key autoincrement,
    time date not null,
    itemid int not null,
    userid int not null,
    state text not null,
    orderid int,
    foreign key(itemid) references stuff(id),
    foreign key(userid) references users(id),
    foreign key(orderid) references orders(id)
);
create table if not exists complaints (
    id integer primary key autoincrement,
    title text not null,
    content text not null,
    time date not null,
    userid integer not null,
    state text not null,
    foreign key(userid) references users(id)
);
