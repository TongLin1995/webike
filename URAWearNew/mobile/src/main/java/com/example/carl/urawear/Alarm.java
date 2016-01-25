package com.example.carl.urawear;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.PowerManager;
import android.util.Log;
import android.view.View;
import android.widget.Toast;

import com.google.android.gms.wearable.DataMap;
import com.mariux.teleport.lib.TeleportClient;

import org.json.JSONException;
import org.json.JSONObject;

public class Alarm extends BroadcastReceiver {

    TeleportClient mTeleportClient;
    TeleportClient.OnGetMessageTask mMessageTask;
    Context mContext;

    final long DumpWindow = 1; // in Mins
    final long AlarmFrequency = 1000 * 60 * 1; // in Secs

    @Override
    public void onReceive(Context context, Intent intent)
    {
        PowerManager pm = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
        PowerManager.WakeLock wl = pm.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "");
        wl.acquire();

        mContext = context;
        if (mTeleportClient != null) {
            mTeleportClient.disconnect();
            mTeleportClient = null;
        }

        mTeleportClient = new TeleportClient(context);
        mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());

        mMessageTask = new ShowToastFromOnGetMessageTask();

        mTeleportClient.setOnGetMessageTask(mMessageTask);

        mTeleportClient.connect();

        wl.release();
    }

    public void SetAlarm(Context context)
    {
        AlarmManager am =( AlarmManager)context.getSystemService(Context.ALARM_SERVICE);
        Intent i = new Intent(context, Alarm.class);
        PendingIntent pi = PendingIntent.getBroadcast(context, 0, i, 0);
        am.setRepeating(AlarmManager.RTC_WAKEUP, System.currentTimeMillis(), AlarmFrequency, pi); // Millisec * Second * Minute

    }

    public void CancelAlarm(Context context)
    {
        Intent intent = new Intent(context, Alarm.class);
        PendingIntent sender = PendingIntent.getBroadcast(context, 0, intent, 0);
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        alarmManager.cancel(sender);

        mTeleportClient.disconnect();
    }

    // Data

    public class ShowToastHelloWorldTask extends TeleportClient.OnSyncDataItemTask {

        @Override
        protected void onPostExecute(DataMap result) {
            String hello = result.getString("hello");

            mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());
        }
    }

    public void parseDataJsonFromWatch(JSONObject dataJSON) {
        try {

            String dataString = "";

            // Heart Rate
            if (!dataJSON.isNull("Heart Rate")) {
                double heartRateReading = dataJSON.getDouble("Heart Rate");
                dataString += "Heart Rate: " + heartRateReading + " ";
            } else {
                dataString += "Heart Rate: " + "null" + " ";
            }

            // Light
            double lightReading = dataJSON.getDouble("Light");
            dataString += "Light: " + lightReading + " ";

            // Magnetic Field
            double magFieldReading = dataJSON.getDouble("Magnetic Field");
            dataString += "Magnetic Field: " + magFieldReading + " ";

            // Gyroscope
            double gyroscopeReading = dataJSON.getDouble("Gyroscope");
            dataString += "Gyroscope: " + gyroscopeReading + " ";

            // Linear Acceleration
            double linearAccelerationReading = dataJSON.getDouble("Linear Acceleration");
            dataString += "Linear Acceleration: " + linearAccelerationReading + " ";

            // Rotation Vector
            double rotationVectorReading = dataJSON.getDouble("Rotation Vector");
            dataString += "Rotation Vector: " + rotationVectorReading + " ";

            // Accelerometer
            double accelerometerReading = dataJSON.getDouble("Accelerometer");
            dataString += "Accelerometer: " + accelerometerReading + " ";

            // Gravity
            double gravityReading = dataJSON.getDouble("Gravity");
            dataString += "Gravity: " + gravityReading + " ";

            // lastUpdate
            String lastUpdate = dataJSON.getString("lastUpdate");
            dataString += "LastUpdate: " + lastUpdate;

            // Send Debug Toast
            Toast.makeText(mContext, "Data" + dataJSON.toString(), Toast.LENGTH_SHORT).show(); // For example
            mTeleportClient.disconnect();
            SaveData(dataString);


        } catch (JSONException e) {
            e.printStackTrace();
        }
    }

    public void SaveData(String data){

        String nowTSAbsolute = URAWearLog.getCurrentTimeStamp();

        URAWearLog.data(nowTSAbsolute, data, this.getClass());
        if (isDumpNeeded()) {
            // Send Debug Toast
            Toast.makeText(mContext, "Dump Needed Write File", Toast.LENGTH_LONG).show();
            URAWearLog.DumpDataLogsToDisk();
        } else {
            // Send Debug Toast
            Toast.makeText(mContext, "No need to dump - DEBUG", Toast.LENGTH_LONG).show();
        }

    }

    public boolean isDumpNeeded(){
        SharedPreferences settings;
        settings = mContext.getSharedPreferences("LAST_DUMP", Context.MODE_PRIVATE);

        URAWearLog.getCurrentTimeStamp();
        long dumpTime = settings.getLong("DUMP_TIME", 0);
        long nowTs = System.currentTimeMillis();
        if (nowTs - dumpTime > DumpWindow * 1000 * 60) {
            SharedPreferences.Editor editor = settings.edit();
            editor.putLong("DUMP_TIME", System.currentTimeMillis());
            editor.commit();
            return true;
        }

        return false;
    }

    //Task that shows the path of a received message
    public class ShowToastFromOnGetMessageTask extends TeleportClient.OnGetMessageTask {

        @Override
        protected void onPostExecute(String path) {

            try {
                JSONObject receivedJSON = new JSONObject(path);
                JSONObject dataJSON = receivedJSON.getJSONObject("Data");
                if (dataJSON != null) {
                    parseDataJsonFromWatch(dataJSON);
                }

            } catch (JSONException e) {
                e.printStackTrace();
            }

            mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());
        }
    }
}
