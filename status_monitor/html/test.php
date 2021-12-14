<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="refresh" content="10">
  <link rel="stylesheet" href="local.css" type="text/css" media="screen" />
  <title>Global Status Monitor: Test Page</title>
</head>
<!-- ================================================================ -->
<?php
include 'inc/base.php';
include 'inc/maindaq_decoder.php';
?>
<!-- ================================================================ -->
<body>
<h1>Global Status Monitor: Test Page</h1>

<div id="panels">
  <div class="panel left"> <hr>
    <span class="last-update">This page last updated:<br /> 
      <b><?php echo date("T Y-m-d (D) H:i:s", $utime_now); ?></b>
    </span>
    <hr>
  </div>
  <div class="panel center"> <hr>
    <?php IncludeStatus("SlowControl_Status.html"); ?>
  </div>
  <div class="panel right"> <hr>
    <?php ShowProblem(); ?>
  </div>
</div> 
</body>
</html>
