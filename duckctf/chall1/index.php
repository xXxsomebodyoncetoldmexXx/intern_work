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

	function check_captcha_checkbox() {
		$url = "https://www.google.com/recaptcha/api/siteverify";
		if (isset($_POST["g-recaptcha-response"])) {
			$fields = [
				"secret" => "6LeyIMEeAAAAAL7mqQraW5WS-ef0Rx2-A433iIMt",
				"response" => $_POST["g-recaptcha-response"]
			];
			$fields_str = http_build_query($fields);

			// Curl
			$ch = curl_init();
			curl_setopt($ch, CURLOPT_URL, $url);
			curl_setopt($ch, CURLOPT_POST, true);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $fields_str);
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

			// resp
			$res = curl_exec($ch);
			curl_close($ch);
			
			$res = json_decode($res);
			if (property_exists($res, "success") && $res->{"success"}) {
				return True;
			}
		} 
		return False;
	}

	function check_captcha_invisible() {
		$url = "https://www.google.com/recaptcha/api/siteverify";
		if (isset($_POST["g-recaptcha-response"])) {
			$fields = [
				"secret" => "6LcVQrIeAAAAACdvERQKFaNlCaaji22p8coOiaF_",
				"response" => $_POST["g-recaptcha-response"]
			];
			$fields_str = http_build_query($fields);

			// Curl
			$ch = curl_init();
			curl_setopt($ch, CURLOPT_URL, $url);
			curl_setopt($ch, CURLOPT_POST, true);
			curl_setopt($ch, CURLOPT_POSTFIELDS, $fields_str);
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

			// resp
			$res = curl_exec($ch);
			curl_close($ch);
			
			$res = json_decode($res);
			if (property_exists($res, "success") && $res->{"success"}) {
				return True;
			}
		} 
		return False;
	}

	$current = null;
	if (isset($_GET['gallery'])) {
		$current = $_GET['gallery'];
	}


	// nav
	echo '<span>';
	$catagories = array('emotes.php', 'computers.php', 'hacking.php', 'upload.php', 'register.php', 'login.php');
	foreach ($catagories as $catagory) {
		$part = explode(".", $catagory);
		if ($current === $catagory) {
			echo "&nbsp;|&nbsp;<span><a href=\"?gallery=$catagory\"><b>$part[0]</b></a></span>";
		} else {
			echo "&nbsp;|&nbsp;<span><a href=\"?gallery=$catagory\">$part[0]</a></span>";
		}
	}
	echo '&nbsp;|</span>';

	// status
	if (isset($_SESSION['username'])) {
		echo "<span style=\"text-align: right; float:right;\">Status : <b>" . htmlentities($_SESSION['username']) . "</b>&nbsp;|&nbsp;<a href=\"logout.php\">Logout</a></span>";
	} else {
		echo "<span style=\"text-align: right; float:right;\">Status : <b>Guest</b>&nbsp;|&nbsp;<a href=\"logout.php\">Logout</a></span>";
	}
	echo '<br /><hr />';

	// content
	if ($current) {
		// LFI prevention
		if ($current == "../index.php") {
			die("Hack detected! This incident will be reported.");
		}
		chdir("./gallery");
		include "$current";
	}
	?>



	<!-- DEBUG -->
	<h3>
	<?php
		// var_dump($_SESSION);
	?>
	</h3>	
</body>
</html>