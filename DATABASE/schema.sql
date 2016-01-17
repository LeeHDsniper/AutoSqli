drop table if exists Autosqli;
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