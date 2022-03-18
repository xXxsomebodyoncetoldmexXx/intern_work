<?php
	$servername = 'localhost';
	$username = 'admin';
	$password = 'password';
	$dbname = 'ImgGalDB';

	$conn = new mysqli($servername, $username, $password, $dbname);
	if ($conn->connect_error) {
		die("Connect to database fail: " . $conn->connect_error);
	}

	// Init table
	$sql = <<<EOL
	CREATE TABLE IF NOT EXISTS users (
	id INTEGER UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	username VARCHAR(30) NOT NULL,
	password VARCHAR(30) NOT NULL,
	reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
	)
	EOL;
	if (!$conn->query($sql)) {
		die('Fail create table: ' . $conn->error);
	}

	function get_user($username, $password) {
		global $conn;
		$sql = "SELECT * FROM users WHERE username=? AND password=?";
		$stmt = $conn->prepare($sql);
		$stmt->bind_param("ss", $username, $password);
		$stmt->execute();
		$result = $stmt->get_result();
		$stmt->close();
		return $result->{"num_rows"} === 1;
	}

	function check_name($username) {
		global $conn;
		$sql = "SELECT * FROM users WHERE username=?";
		$stmt = $conn->prepare($sql);
		$stmt->bind_param("s", $username);
		$stmt->execute();
		$result = $stmt->get_result();
		$stmt->close();
		return $result->{"num_rows"} === 0;
	}

	function insert_user($username, $password) {
		global $conn;
		$sql = "INSERT INTO users (username, password) VALUES (?, ?)";
		$stmt = $conn->prepare($sql);
		$stmt->bind_param("ss", $username, $password);
		$result = $stmt->execute();
		$stmt->close();
		return $result;
	}
?>