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

  function err($msg) {
    echo "<h3 style='color:red;'>" . htmlentities($msg) . "</h3>";
    die();
  }

	include 'db.php';

  echo '<span>&nbsp;|&nbsp;<span><a href=/>home</a></span>';
	$actions = array('register', 'login');
	foreach ($actions as $action) {
    echo "&nbsp;|&nbsp;<span><a href=\"?action=$action\">$action</a></span>";
	}
	echo '&nbsp;|</span>';

  // status
	if (empty($_SESSION['username'])) {
    echo "<span style=\"text-align: right; float:right;\">Status : <b>Guest</b>&nbsp;|&nbsp;<a href=\"logout.php\">Logout</a></span>";
	} else {
		echo "<span style=\"text-align: right; float:right;\">Status : <b>" . htmlentities($_SESSION['username']) . "</b>&nbsp;|&nbsp;<a href=\"logout.php\">Logout</a></span>";
	}
	echo '<br /><hr />';

  include 'main.php';
	?>

</body>
</html>