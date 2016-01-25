package com.example.carl.urawear;

import android.app.Notification;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.IBinder;
import android.support.v4.app.NotificationCompat;
import android.util.Log;
import android.widget.Toast;

import com.google.android.gms.wearable.DataMap;
import com.google.android.gms.wearable.Wearable;
import com.mariux.teleport.lib.TeleportClient;

import java.text.SimpleDateFormat;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Vector;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import com.mariux.teleport.lib.TeleportClient;
import com.mariux.teleport.lib.TeleportService;

import org.json.JSONException;
import org.json.JSONObject;

public class SensorService extends TeleportService implements SensorEventListener {
    private static final String TAG = "SensorService";

    // For storing sensors' data
    public HashMap<String, Float> mDataMap;
    public Vector<String> mAvailableSensors;

    // All sensors' LABEL
    private final static int SENS_ACCELEROMETER = Sensor.TYPE_ACCELEROMETER;
    private final static int SENS_MAGNETIC_FIELD = Sensor.TYPE_MAGNETIC_FIELD;
    // 3 = @Deprecated Orientation
    private final static int SENS_GYROSCOPE = Sensor.TYPE_GYROSCOPE;
    private final static int SENS_LIGHT = Sensor.TYPE_LIGHT;
    private final static int SENS_PRESSURE = Sensor.TYPE_PRESSURE;
    // 7 = @Deprecated Temperature
    private final static int SENS_PROXIMITY = Sensor.TYPE_PROXIMITY;
    private final static int SENS_GRAVITY = Sensor.TYPE_GRAVITY;
    private final static int SENS_LINEAR_ACCELERATION = Sensor.TYPE_LINEAR_ACCELERATION;
    private final static int SENS_ROTATION_VECTOR = Sensor.TYPE_ROTATION_VECTOR;
    private final static int SENS_HUMIDITY = Sensor.TYPE_RELATIVE_HUMIDITY;
    // TODO: there's no Android Wear devices yet with a body temperature monitor
    private final static int SENS_AMBIENT_TEMPERATURE = Sensor.TYPE_AMBIENT_TEMPERATURE;
    private final static int SENS_MAGNETIC_FIELD_UNCALIBRATED = Sensor.TYPE_MAGNETIC_FIELD_UNCALIBRATED;
    private final static int SENS_GAME_ROTATION_VECTOR = Sensor.TYPE_GAME_ROTATION_VECTOR;
    private final static int SENS_GYROSCOPE_UNCALIBRATED = Sensor.TYPE_GYROSCOPE_UNCALIBRATED;
    private final static int SENS_SIGNIFICANT_MOTION = Sensor.TYPE_SIGNIFICANT_MOTION;
    private final static int SENS_STEP_DETECTOR = Sensor.TYPE_STEP_DETECTOR;
    private final static int SENS_STEP_COUNTER = Sensor.TYPE_STEP_COUNTER;
    private final static int SENS_GEOMAGNETIC = Sensor.TYPE_GEOMAGNETIC_ROTATION_VECTOR;
    private final static int SENS_HEARTRATE = Sensor.TYPE_HEART_RATE;

    // Sensor Manager
    SensorManager mSensorManager;
    private Sensor mHeartrateSensor;
    SensorNames mSensorNames;

    // Sensor Log Timer
    Timer sensorLogTimer;
    final long DATA_TO_PHONE_FREQUENCY = 1000 * 60; // in milliseconds
    final long GET_SENSOR_DATA_FREQUENCY = 1000 * 60; // in milliseconds
    // How long will the window stays
    final long GET_SENSOR_DATA_PERIOD = 1000 * 30; // in milliseconds
    // Heart Rate Flag
    private static Boolean isHeartRateNew = false;
    private static Boolean isHeartSensorScheduled = false;

    // Communication manager (between phone and watch)
    TeleportClient mTeleportClient;
    TeleportClient.OnGetMessageTask mMessageTask;

    // Battery Level
    Integer mBatteryLevel = 0;

    @Override
    public void onCreate() {
        super.onCreate();

        // Close connection between phone if there's one
        if (mTeleportClient != null) {
            stopMeasurement();
            mTeleportClient.disconnect();
            mTeleportClient = null;
        }

        // New Connection Client
        mTeleportClient = new TeleportClient(this);
        mMessageTask = new ShowToastFromOnGetMessageTask();
        mTeleportClient.setOnGetMessageTask(mMessageTask);
        mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());
        mTeleportClient.connect();

        // Sensor DataHolder
        mSensorNames = new SensorNames();
        mDataMap = new HashMap<>();
        mAvailableSensors = new Vector<>();

        // Build Notificaiton app on watch
        NotificationCompat.Builder notificationBuilder =
                new NotificationCompat.Builder(this)
                        .setSmallIcon(R.drawable.bike)
                        .setContentTitle("WeBike Wear")
                        .setContentText("Collecting sensor data..");


        // Create second page notification
        Notification secondPageNotification =
                new NotificationCompat.Builder(this)
                        .setSmallIcon(R.mipmap.ic_launcher)
                        .setContentTitle("HeartRate")
                        .build();

        notificationBuilder.extend(new NotificationCompat.WearableExtender().addPage(secondPageNotification));

        startForeground(1, notificationBuilder.build());

        // Init Timer
        if (sensorLogTimer == null) {
            sensorLogTimer = new Timer();
            TimerTask mearsurementTask = new StartMeasurementTimerTask();
            sensorLogTimer.scheduleAtFixedRate(mearsurementTask, 0, GET_SENSOR_DATA_FREQUENCY);

            TimerTask updateNotification = new UpdateNotificationTimerTask();
            sensorLogTimer.scheduleAtFixedRate(updateNotification, 0, DATA_TO_PHONE_FREQUENCY);
        }
    }

    public void retrieveTripInfo(){
        SharedPreferences settings;
        settings = getSharedPreferences("TRIP_INFO", Context.MODE_PRIVATE);

        String tripStartTime = settings.getString("START_TIME", "");
        Boolean isTripStart = settings.getBoolean("IS_TRIP_START", false);

        if (isTripStart) {
            Toast.makeText(getApplicationContext(), "Trip starts at:  " + tripStartTime, Toast.LENGTH_SHORT).show();
        } else {
            Toast.makeText(getApplicationContext(), "Trip ends at:  " + tripStartTime, Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        stopMeasurement();
        mTeleportClient.disconnect();
        sensorLogTimer.cancel();
    }

    public class StartMeasurementTimerTask extends TimerTask {
        @Override
        public void run() {
            startMeasurement();
            TimerTask stopMeasurementTask = new StopMeasurementTimerTask();
            sensorLogTimer.schedule(stopMeasurementTask, GET_SENSOR_DATA_PERIOD);
        }
    }

    public class StopMeasurementTimerTask extends TimerTask {
        @Override
        public void run() {
            stopMeasurement();
        }
    }

    protected void startMeasurement() {

        // Sensor Manager
        mSensorManager = ((SensorManager) getSystemService(SENSOR_SERVICE));
        // Init Heart Rate Boolean
        isHeartRateNew = false;

        Sensor accelerometerSensor = mSensorManager.getDefaultSensor(SENS_ACCELEROMETER);
        Sensor ambientTemperatureSensor = mSensorManager.getDefaultSensor(SENS_AMBIENT_TEMPERATURE);
        Sensor gameRotationVectorSensor = mSensorManager.getDefaultSensor(SENS_GAME_ROTATION_VECTOR);
        Sensor geomagneticSensor = mSensorManager.getDefaultSensor(SENS_GEOMAGNETIC);
        Sensor gravitySensor = mSensorManager.getDefaultSensor(SENS_GRAVITY);
        Sensor gyroscopeSensor = mSensorManager.getDefaultSensor(SENS_GYROSCOPE);
        Sensor gyroscopeUncalibratedSensor = mSensorManager.getDefaultSensor(SENS_GYROSCOPE_UNCALIBRATED);
        mHeartrateSensor = mSensorManager.getDefaultSensor(SENS_HEARTRATE);
        Sensor heartrateSamsungSensor = mSensorManager.getDefaultSensor(65562);
        Sensor lightSensor = mSensorManager.getDefaultSensor(SENS_LIGHT);
        Sensor linearAccelerationSensor = mSensorManager.getDefaultSensor(SENS_LINEAR_ACCELERATION);
        Sensor magneticFieldSensor = mSensorManager.getDefaultSensor(SENS_MAGNETIC_FIELD);
        Sensor magneticFieldUncalibratedSensor = mSensorManager.getDefaultSensor(SENS_MAGNETIC_FIELD_UNCALIBRATED);
        Sensor pressureSensor = mSensorManager.getDefaultSensor(SENS_PRESSURE);
        Sensor proximitySensor = mSensorManager.getDefaultSensor(SENS_PROXIMITY);
        Sensor humiditySensor = mSensorManager.getDefaultSensor(SENS_HUMIDITY);
        Sensor rotationVectorSensor = mSensorManager.getDefaultSensor(SENS_ROTATION_VECTOR);
        Sensor significantMotionSensor = mSensorManager.getDefaultSensor(SENS_SIGNIFICANT_MOTION);
        Sensor stepCounterSensor = mSensorManager.getDefaultSensor(SENS_STEP_COUNTER);
        Sensor stepDetectorSensor = mSensorManager.getDefaultSensor(SENS_STEP_DETECTOR);


        // Register the listener
        if (mSensorManager != null) {
            if (accelerometerSensor != null) {
                mSensorManager.registerListener(this, accelerometerSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_ACCELEROMETER));
            } else {
                Log.w(TAG, "No Accelerometer found");
            }

            if (ambientTemperatureSensor != null) {
                mSensorManager.registerListener(this, ambientTemperatureSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_AMBIENT_TEMPERATURE));
            } else {
                Log.w(TAG, "Ambient Temperature Sensor not found");
            }

            if (gameRotationVectorSensor != null) {
                mSensorManager.registerListener(this, gameRotationVectorSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_GAME_ROTATION_VECTOR));
            } else {
                Log.w(TAG, "Gaming Rotation Vector Sensor not found");
            }

            if (geomagneticSensor != null) {
                mSensorManager.registerListener(this, geomagneticSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_GEOMAGNETIC));
            } else {
                Log.w(TAG, "No Geomagnetic Sensor found");
            }

            if (gravitySensor != null) {
                mSensorManager.registerListener(this, gravitySensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_GRAVITY));
            } else {
                Log.w(TAG, "No Gravity Sensor");
            }

            if (gyroscopeSensor != null) {
                mSensorManager.registerListener(this, gyroscopeSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_GYROSCOPE));
            } else {
                Log.w(TAG, "No Gyroscope Sensor found");
            }

            if (gyroscopeUncalibratedSensor != null) {
                mSensorManager.registerListener(this, gyroscopeUncalibratedSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_GYROSCOPE_UNCALIBRATED));
            } else {
                Log.w(TAG, "No Uncalibrated Gyroscope Sensor found");
            }

            if (mHeartrateSensor != null && !isHeartSensorScheduled) {
                // Heart Rate Schedule
                final int measurementDuration   = 10;   // Seconds
                final int measurementBreak      = 5;    // Seconds

                ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
                scheduler.scheduleAtFixedRate(
                        new Runnable() {
                            @Override
                            public void run() {
                                Log.d(TAG, "register Heartrate Sensor");
                                mSensorManager.registerListener(SensorService.this, mHeartrateSensor, SensorManager.SENSOR_DELAY_NORMAL);
                                mAvailableSensors.add(mSensorNames.getName(SENS_HEARTRATE));

                                try {
                                    Thread.sleep(measurementDuration * 1000);
                                } catch (InterruptedException e) {
                                    Log.e(TAG, "Interrupted while waitting to unregister Heartrate Sensor");
                                }

                                Log.d(TAG, "unregister Heartrate Sensor");
                                mSensorManager.unregisterListener(SensorService.this, mHeartrateSensor);
                            }
                        }, 3, measurementDuration + measurementBreak, TimeUnit.SECONDS);
                isHeartSensorScheduled = true;
            } else {
                Log.d(TAG, "No Heartrate Sensor found");
            }

            if (heartrateSamsungSensor != null) {
                mSensorManager.registerListener(this, heartrateSamsungSensor, SensorManager.SENSOR_DELAY_FASTEST);
//                mAvailableSensors.add(mSensorNames.getName(65562));
            } else {
                Log.d(TAG, "Samsungs Heartrate Sensor not found");
            }

            if (lightSensor != null) {
                mSensorManager.registerListener(this, lightSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_LIGHT));
            } else {
                Log.d(TAG, "No Light Sensor found");
            }

            if (linearAccelerationSensor != null) {
                mSensorManager.registerListener(this, linearAccelerationSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_LINEAR_ACCELERATION));
            } else {
                Log.d(TAG, "No Linear Acceleration Sensor found");
            }

            if (magneticFieldSensor != null) {
                mSensorManager.registerListener(this, magneticFieldSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_MAGNETIC_FIELD));
            } else {
                Log.d(TAG, "No Magnetic Field Sensor found");
            }

            if (magneticFieldUncalibratedSensor != null) {
                mSensorManager.registerListener(this, magneticFieldUncalibratedSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_MAGNETIC_FIELD_UNCALIBRATED));
            } else {
                Log.d(TAG, "No uncalibrated Magnetic Field Sensor found");
            }

            if (pressureSensor != null) {
                mSensorManager.registerListener(this, pressureSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_PRESSURE));
            } else {
                Log.d(TAG, "No Pressure Sensor found");
            }

            if (proximitySensor != null) {
                mSensorManager.registerListener(this, proximitySensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_PROXIMITY));
            } else {
                Log.d(TAG, "No Proximity Sensor found");
            }

            if (humiditySensor != null) {
                mSensorManager.registerListener(this, humiditySensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_HUMIDITY));
            } else {
                Log.d(TAG, "No Humidity Sensor found");
            }

            if (rotationVectorSensor != null) {
                mSensorManager.registerListener(this, rotationVectorSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_ROTATION_VECTOR));
            } else {
                Log.d(TAG, "No Rotation Vector Sensor found");
            }

            if (significantMotionSensor != null) {
                mSensorManager.registerListener(this, significantMotionSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_SIGNIFICANT_MOTION));
            } else {
                Log.d(TAG, "No Significant Motion Sensor found");
            }

            if (stepCounterSensor != null) {
                mSensorManager.registerListener(this, stepCounterSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_STEP_COUNTER));
            } else {
                Log.d(TAG, "No Step Counter Sensor found");
            }

            if (stepDetectorSensor != null) {
                mSensorManager.registerListener(this, stepDetectorSensor, SensorManager.SENSOR_DELAY_NORMAL);
                mAvailableSensors.add(mSensorNames.getName(SENS_STEP_DETECTOR));
            } else {
                Log.d(TAG, "No Step Detector Sensor found");
            }
        }
    }

    private void stopMeasurement() {
        if (mSensorManager != null)
            mSensorManager.unregisterListener(this);
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        if (event != null) {
            String sensorName = mSensorNames.getName(event.sensor.getType());
            Float sensorReading = event.values[0];
            if (event.sensor.getType() == SENS_HEARTRATE) {
                if (sensorReading > 0) {
                    mDataMap.put(sensorName, sensorReading);
                    isHeartRateNew = true;
                } else if (!isHeartRateNew){
                    // Only set the heart rate to 0 if there's
                    // no heart rate sensed in a window period
                    mDataMap.put(sensorName, sensorReading);
                }
            } else {
                mDataMap.put(sensorName, sensorReading);
            }
        }
    }

    // update Watch notification UI
    void updateNotification() {
        NotificationManager mNotificationManager =
                (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);

        Calendar c = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("dd:MMMM:yyyy HH:mm:ss ");
        String strDate = sdf.format(c.getTime());

        Bitmap icon = BitmapFactory.decodeResource(this.getResources(),
                R.drawable.icon);

        NotificationCompat.Builder notificationBuilder =
                new NotificationCompat.Builder(this)
                        .setSmallIcon(R.drawable.bike)
                        .setContentTitle("WeBike Wear")
                        .setContentText("Updated At: " + strDate);


        List<Notification> notificationList = new Vector<>();

        // Create battery level page
        Notification bLevelPageNotification =
                new NotificationCompat.Builder(this)
                        .setContentTitle("Battery Level")
                        .setContentText("Battery: " + mBatteryLevel + " Updated At: " + strDate)
                        .build();
        notificationList.add(bLevelPageNotification);

        for (int i = 0; i < 8; i++) {
            String sensorName = getSensorNameByIndex(i);
            Float sensorReading = mDataMap.get(sensorName);

            // Create second page notification
            Notification secondPageNotification =
                    new NotificationCompat.Builder(this)
                            .setContentTitle(sensorName)
                            .setContentText("Reading: " + sensorReading)
                            .build();
            notificationList.add(secondPageNotification);
        }

        Intent actionIntent = new Intent(this, MainActivity.class).putExtra("FromNotification", true);
        PendingIntent actionPendingIntent =
                PendingIntent.getActivity(this, 0, actionIntent,
                        PendingIntent.FLAG_UPDATE_CURRENT);
        NotificationCompat.Action action =
                new NotificationCompat.Action.Builder(R.drawable.bike,
                        "Start Trip", actionPendingIntent)
                        .build();

        notificationBuilder.extend(new NotificationCompat.WearableExtender().addPages(notificationList).setBackground(icon).addAction(action));

        int notifyID = 1;

        // Because the ID remains unchanged, the existing notification is
        // updated.
        mNotificationManager.notify(
                notifyID,
                notificationBuilder.build());
    }

    String getSensorNameByIndex(int index) {
        switch (index) {
            case 0:
                return "Heart Rate";
            case 1:
                return "Light";
            case 2:
                return "Magnetic Field";
            case 3:
                return "Gyroscope";
            case 4:
                return "Linear Acceleration";
            case 5:
                return "Rotation Vector";
            case 6:
                return "Accelerometer";
            default:
                return "Gravity";
        }
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

    }

    // update notification task
    public class UpdateNotificationTimerTask extends TimerTask {
        @Override
        public void run() {
            // Update notification
            updateNotification();
            // Sync Data with Phone
            sendDataToPhone();
        }
    }

    // Send logged data to phone
    public void sendDataToPhone() {
        try {
            JSONObject mainJson = new JSONObject();
            JSONObject dataJson = new JSONObject();

            for (int i = 0; i < 8; i++) {
                String sensorName = getSensorNameByIndex(i);
                Float sensorReading = mDataMap.get(sensorName);
                dataJson.put(sensorName, sensorReading);
            }

            Calendar c = Calendar.getInstance();
            SimpleDateFormat sdf = new SimpleDateFormat("dd:MMMM:yyyy HH:mm:ss ");
            String strDate = sdf.format(c.getTime());

            dataJson.put("lastUpdate", strDate);

            mainJson.put("Data", dataJson);

            mTeleportClient.sendMessage(mainJson.toString(2), null);
            Log.w(TAG, "Send Data To Phone");
//            mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());
        }
        catch (JSONException e) {
            e.printStackTrace();
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

    //Task that shows the path of a received message
    public class ShowToastFromOnGetMessageTask extends TeleportClient.OnGetMessageTask {

        @Override
        protected void onPostExecute(String  path) {
            if (path.equalsIgnoreCase("From Device")) {
                Toast.makeText(getApplicationContext(),"Message - "+path,Toast.LENGTH_SHORT).show();
            } else {
                String newBatteryLevel = path;
                mBatteryLevel = Integer.parseInt(newBatteryLevel);
                Toast.makeText(getApplicationContext(), "new battery level: " + newBatteryLevel, Toast.LENGTH_SHORT).show();
            }

            //let's reset the task (otherwise it will be executed only once)
            mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());
        }
    }
}
