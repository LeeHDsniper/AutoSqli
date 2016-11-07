drop table if exists Autosqli;
drop table if exists SuccessTarget;
create table Autosqli (
  id integer primary key autoincrement,
  taskid string not null,
  url string null,
  url_parameters string null,
  options string null,
  log string null,
  status string null,
  data string null,
  user string null,
  server string null
);
create table SuccessTarget (
  id integer primary key autoincrement,
  url string null,
  data string null,
  user string null
);