<?php
  $servername = 'localhost';
  $username = 'admin3';
  $password = 'password';
  $dbname = 'MsgDB';

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
  isadmin BOOL DEFAULT FALSE,
  reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
  )
  EOL;
  if (!$conn->query($sql)) {
    die('Fail create users table: ' . $conn->error);
  }

  // Init table
  $sql = <<<EOL
  CREATE TABLE IF NOT EXISTS msgs (
  id INTEGER UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title TEXT NOT NULL,
  content MEDIUMTEXT NOT NULL,
  sender INTEGER UNSIGNED NOT NULL,
  receiver INTEGER UNSIGNED NOT NULL,
  FOREIGN KEY (sender) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
  FOREIGN KEY (receiver) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE,
  reg_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
  )
  EOL;  
  if (!$conn->query($sql)) {
    die('Fail create msgs table: ' . $conn->error);
  }

  function get_user($username, $password) {
    global $conn;
    $sql = "SELECT * FROM users WHERE username=? AND password=?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ss", $username, $password);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
  }

  function get_user_by_name($username) {
    global $conn;
    $sql = "SELECT * FROM users WHERE username=?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("s", $username);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
  }

  function get_user_by_id($uid) {
    global $conn;
    $sql = "SELECT * FROM users WHERE id=?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("i", $uid);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
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

  function get_msg() {
    global $conn;
    $sql = "SELECT * FROM msgs";
    $result = $conn->query($sql);
    return $result;    
  }

  function get_own_msg($uid) {
    global $conn;
    $sql = "SELECT * FROM msgs WHERE receiver=?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("i", $uid);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
  }

  function get_msg_by_id($mid) {
    global $conn;
    $sql = "SELECT * FROM msgs WHERE id=?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("i", $mid);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
  }

  function insert_msg($title, $content, $sender, $recv) {
    global $conn;
    $sql = "INSERT INTO msgs (title, content, sender, receiver) VALUES (?, ?, ?, ?)";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("ssii", $title, $content, $sender, $recv);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
  }

  function delete_msg($mid) {
    global $conn;
    $sql = "DELETE FROM msgs WHERE id=?";
    $stmt = $conn->prepare($sql);
    $stmt->bind_param("i", $mid);
    $stmt->execute();
    $result = $stmt->get_result();
    $stmt->close();
    return $result;
  }
?>