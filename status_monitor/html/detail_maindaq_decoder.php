<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="refresh" content="10">
  <link rel="stylesheet" href="local.css" type="text/css" media="screen" />
  <title>Detail Page &mdash; MainDAQ Decoder Status</title>
</head>

<body>
<h1>Detail Page &mdash; MainDAQ Decoder Status</h1>
<div class="panel50 left">

<h2>Status Summary</h2>
<!-- ================================================================ -->
<?php
include 'inc/base.php';
include 'inc/maindaq_decoder.php';

MakeConnection($sqlcon, $server);
SelectDB('user_e1039_maindaq', $sqlcon);
MainDaqDecoderSummary($sqlcon);

$list_error_type = array(
  0 => array( 'WORD_ONLY89'    , 'ROC got stuck.  VME crate has to be reset.' ),
  1 => array( 'WORD_OVERFLOW'  , 'N of words expected on a TDC exceeds N of words available on this ROC.' ),
  2 => array( 'MULTIPLE_HEADER', 'Header words (= stop hits) appear twice or more before the event-ID word appears.' ),
  3 => array( 'EVT_ID_ONLY'    , 'An event-ID word appears with no preceding header word.' ),
  4 => array( 'START_WO_STOP'  , 'A hit word (=start) appears with no preceding header word.' ),
  5 => array( 'START_NOT_RISE' , 'A hit word is not of rising edge.' ),
  6 => array( 'DIRTY_FINISH'   , 'A header word appears but no event-ID word appears upto the end of word set.' ),
  7 => array( 'V1495_0BAD'     , 'N of words coming from V1495 TDC board is too large.' ),
);
?>
<!-- ================================================================ -->

<h2>TDC Errors Observed</h2>
<table>
<tr> <th>ROC ID</th> <th>E#</th> <th>Error Type</th> <th>Count</th> <th>Min Event ID</th> <th>Max Event ID</th> </tr>
<!-- ================================================================ -->
<?php

$comm = "select max(run_id) from deco_error_info";
$result = mysql_query($comm, $sqlcon) or die("!!ERROR!!  Failed in executing query: ".$comm);
$row = mysql_fetch_array($result);
$run = $row[0];

$comm = "select * from deco_error_tdc where run_id = ".$run;
$result = mysql_query($comm, $sqlcon) or die("!!ERROR!!  Failed in executing query: ".$comm);
while ($row = mysql_fetch_assoc($result)) {
  $err_id = $row['error_id'];
  echo '<tr><td>',$row['roc_id'],'</td><td>',$err_id,'</td><td>',$list_error_type[$err_id][0],'</td><td>',$row['error_count'],'</td><td>',$row['event_id_min'],'</td><td>',$row['event_id_max'],'</tr>';
}
?>
<!-- ================================================================ -->
</table>

</div>
<div class="panel50 right">

<h2>Explanation of TDC Error Type</h2>
<table>
<tr> <th>#</th> <th>Short Desc.</th> <th>Long Description</th> </tr>
<!-- ================================================================ -->
<?php
foreach (array_keys($list_error_type) as $id) {
  echo '<tr><th>',$id,'</th><td>',$list_error_type[$id][0],'</td><td>',$list_error_type[$id][1],'</td></tr>';
}
?>
<!-- ================================================================ -->
</table>

</div> 
</body>
</html>
