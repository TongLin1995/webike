package com.example.carl.urawear;

import android.content.Intent;
import android.support.v7.app.ActionBarActivity;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.wearable.DataMap;
import com.mariux.teleport.lib.TeleportClient;

import org.json.JSONException;
import org.json.JSONObject;


public class MainActivity extends ActionBarActivity {

    private static final String TAG = "URA Device";

    TeleportClient mTeleportClient;
    TeleportClient.OnGetMessageTask mMessageTask;

    private TextView mHeartRateView;
    private TextView mGravityTextView;
    private TextView mLightTextView;
    private TextView mMagFieldTextView;
    private TextView mGyroscopeTextView;
    private TextView mLinearAccTextView;
    private TextView mRotationVecTextView;
    private TextView mAccelerometerTextView;
    private TextView mLastUpdateTextView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        mHeartRateView = (TextView)findViewById(R.id.text1);
        mGravityTextView = (TextView)findViewById(R.id.gravityView);
        mLightTextView = (TextView)findViewById(R.id.LightTextView);
        mMagFieldTextView = (TextView)findViewById(R.id.MagFieldTextView);
        mGyroscopeTextView = (TextView)findViewById(R.id.GyroScopeTextView);
        mLinearAccTextView = (TextView)findViewById(R.id.LinearAccelerationTextView);
        mRotationVecTextView = (TextView)findViewById(R.id.RotationVectorTextView);
        mAccelerometerTextView = (TextView)findViewById(R.id.AccelerometerTextView);
        mLastUpdateTextView = (TextView)findViewById(R.id.LastUpdateTextView);

        mTeleportClient = new TeleportClient(this);
        mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());

        mMessageTask = new ShowToastFromOnGetMessageTask();

        mTeleportClient.setOnGetMessageTask(mMessageTask);

        // For Debugging Only
//        Intent i= new Intent(this, URAWearService.class);
//        startService(i);
    }


    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        // Handle action bar item clicks here. The action bar will
        // automatically handle clicks on the Home/Up button, so long
        // as you specify a parent activity in AndroidManifest.xml.
        int id = item.getItemId();

        //noinspection SimplifiableIfStatement
        if (id == R.id.action_settings) {
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    @Override
    protected void onStart() {
        super.onStart();
        mTeleportClient.connect();
    }

    @Override
    protected void onStop() {
        super.onStop();
        mTeleportClient.disconnect();
    }


    public void syncDataItem(View v) {
        //Let's sync a String!
//        mTeleportClient.syncString("hello", "Hello, World!");
        if (mTeleportClient != null) {
            mTeleportClient.connect();
            mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());
            mTeleportClient.syncString("hello", "Hello, World!");
        } else {
//            mTeleportClient = new TeleportClient(this);
            mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());
//            mTeleportClient.connect();
            mTeleportClient.syncString("hello", "Hello, World!");
        }
    }

    public void sendMessage(View v) {

        mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());

        mTeleportClient.sendMessage("From Device", null);
    }

    public void onBtnClicked(View v){
        if(v.getId() == R.id.button1){
            //handle the click here
//            sendMessage(v);
            syncDataItem(v);
//            mTeleportClient.syncString("hello", "Hello, World!");
        } else if (v.getId() == R.id.button2){
//            mTeleportClient.syncInt("BatteryLevel", 0);
            mTeleportClient.sendMessage("0", null);
        } else if (v.getId() == R.id.button3){
//            mTeleportClient.syncInt("BatteryLevel", 50);
            mTeleportClient.sendMessage("50", null);
        } else if (v.getId() == R.id.button4){
//            mTeleportClient.syncInt("BatteryLevel", 100);
            mTeleportClient.sendMessage("100", null);
        }
    }

    public class ShowToastHelloWorldTask extends TeleportClient.OnSyncDataItemTask {

        @Override
        protected void onPostExecute(DataMap result) {
            String hello = result.getString("hello");

            Toast.makeText(getApplicationContext(), hello, Toast.LENGTH_SHORT).show();

            mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());
        }
    }

    public void parseDataJsonFromWatch(JSONObject dataJSON) {
        try {

            // Heart Rate
            if (!dataJSON.isNull("Heart Rate")) {
                double heartRateReading = dataJSON.getDouble("Heart Rate");
                mHeartRateView.setText("Heart Rate: " + heartRateReading);
            } else {
                mHeartRateView.setText("Heart Rate: " + "null");
            }

            // Light
            double lightReading = dataJSON.getDouble("Light");
            mLightTextView.setText("Light: " + lightReading);

            // Magnetic Field
            double magFieldReading = dataJSON.getDouble("Magnetic Field");
            mMagFieldTextView.setText("Magnetic Field: " + magFieldReading);

            // Gyroscope
            double gyroscopeReading = dataJSON.getDouble("Gyroscope");
            mGyroscopeTextView.setText("Gyroscope: " + gyroscopeReading);

            // Linear Acceleration
            double linearAccelerationReading = dataJSON.getDouble("Linear Acceleration");
            mLinearAccTextView.setText("Linear Acceleration: " + linearAccelerationReading);

            // Rotation Vector
            double rotationVectorReading = dataJSON.getDouble("Rotation Vector");
            mRotationVecTextView.setText("Rotation Vector: " + rotationVectorReading);

            // Accelerometer
            double accelerometerReading = dataJSON.getDouble("Accelerometer");
            mAccelerometerTextView.setText("Accelerometer: " + accelerometerReading);

            // Gravity
            double gravityReading = dataJSON.getDouble("Gravity");
            mGravityTextView.setText("Gravity: " + gravityReading);

            // lastUpdate
            String lastUpdate = dataJSON.getString("lastUpdate");
            mLastUpdateTextView.setText("Last Update: " + lastUpdate);


        } catch (JSONException e) {
            e.printStackTrace();
        }
    }


    //Task that shows the path of a received message
    public class ShowToastFromOnGetMessageTask extends TeleportClient.OnGetMessageTask {

        @Override
        protected void onPostExecute(String path) {

            try {
                JSONObject receivedJSON = new JSONObject(path);
//                receivedJSON.get
                JSONObject dataJSON = receivedJSON.getJSONObject("Data");
                if (dataJSON != null) {
                    parseDataJsonFromWatch(dataJSON);
                }

            } catch (JSONException e) {
                Toast.makeText(getApplicationContext(),"Message - "+path,Toast.LENGTH_SHORT).show();
                e.printStackTrace();
            }

            //let's reset the task (otherwise it will be executed only once)
            mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());
        }
    }

}
