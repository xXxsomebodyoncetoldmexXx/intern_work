<?php session_start() ?>
<!DOCTYPE html>
<html>
<head>
	<title>Duck CTF</title>
</head>
<body>
	<link rel="stylesheet" property="stylesheet" type="text/css" href="s.css" media="all">
	<iframe src="iframe.html"></iframe>

	<h1>Image Gallery</h1>
	<?php
	error_reporting(E_ALL);
	ini_set('display_errors', '1');
	include 'db.php';

  echo "<span>&nbsp;|&nbsp;<a href=\"/\"><b>Home</b></a>&nbsp;|</span>";

	// status
	if (empty($_SESSION['username'])) {
    echo "<span style=\"text-align: right; float:right;\">Status : <b>Guest</b>&nbsp;|&nbsp;<a href=\"logout.php\">Logout</a></span>";
	} else {
    echo "<span>&nbsp;<a href=\"/?action=add\"><b>Add news</b></a>&nbsp;|</span>";
		echo "<span style=\"text-align: right; float:right;\">Status : <b>" . htmlentities($_SESSION['username']) . "</b>&nbsp;|&nbsp;<a href=\"logout.php\">Logout</a></span>";
	}
	echo '<br /><hr />';


  // login
  if (empty($_SESSION['login'])) {
    include 'login.php';
  } else {
    if (empty($_GET['action'])){
      include 'main.php';
    } elseif ($_GET['action'] === 'add') {
      include 'add-article.php';
    } elseif ($_GET['action'] === 'update') {
      include 'update-article.php';
    } elseif ($_GET['action'] === 'delete') {
      include 'delete-article.php';
    }
  }
	?>
</body>
</html>