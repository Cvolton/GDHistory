<?php
//error_reporting(0);
include dirname(__FILE__)."/../config/connection.php";
@header('Content-Type: text/html; charset=utf-8');
try {
    $db = new PDO("mysql:host=$hostname;port=$port;dbname=$dbname", $username, $password, array(
    PDO::ATTR_PERSISTENT => true
));
    // set the PDO error mode to exception
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->setAttribute( PDO::ATTR_EMULATE_PREPARES, false );
    }
catch(PDOException $e)
    {
    echo "Connection failed: " . $e->getMessage();
    }
?>