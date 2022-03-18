<?php
	$servername = 'localhost';
	$username = 'admin2';
	$password = 'password';
	$dbname = 'NewsDB';

	$conn = new mysqli($servername, $username, $password, $dbname);
	if ($conn->connect_error) {
		die("Connect to database fail: " . $conn->connect_error);
	}

	// Init table
	$sql = <<<EOL
	CREATE TABLE IF NOT EXISTS news (
	id INTEGER UNSIGNED AUTO_INCREMENT PRIMARY KEY,
	title TEXT NOT NULL,
	author TEXT NOT NULL,
	content MEDIUMTEXT NOT NULL,
	date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
	)
	EOL;
	if (!$conn->query($sql)) {
		die('Fail create table: ' . $conn->error);
	}

	function get_news() {
		global $conn;
		$sql = "SELECT * FROM news";
		$result = $conn->query($sql);
		return $result;
	}

  function get_news_id($id) {
    global $conn;
    $sql = "SELECT * FROM news WHERE id=?";
    $stmt = $conn->prepare($sql);
		$stmt->bind_param("i", $id);
		$stmt->execute();
		$result = $stmt->get_result();
		$stmt->close();
		return $result;
  }

  function insert_news($title, $author, $content) {
    global $conn;
    $sql = "INSERT INTO news (title, author, content) VALUES ('$title', '$author', '$content')";
    $result = $conn->query($sql);
    return $result;
  }

  function update_news($id, $title, $content) {
    global $conn;
    $sql = "UPDATE news SET title=?, content=? WHERE id=?";
    $stmt = $conn->prepare($sql);
		$stmt->bind_param("ssi", $title, $content, $id);
		$stmt->execute();
		$result = $stmt->get_result();
		$stmt->close();
		return $result;
  }

  function delete_news($id) {
    global $conn;
    $sql = "DELETE FROM news WHERE id=?";
    $stmt = $conn->prepare($sql);
		$stmt->bind_param("i", $id);
		$stmt->execute();
		$result = $stmt->get_result();
		$stmt->close();
		return $result;
  }
?>