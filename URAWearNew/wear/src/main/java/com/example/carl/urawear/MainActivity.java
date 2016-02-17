package com.example.carl.urawear;

import android.app.Notification;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.hardware.Sensor;
import android.app.Activity;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.Bundle;
//import android.support.wearable.activity.WearableActivity;
import android.support.wearable.view.BoxInsetLayout;
import android.support.wearable.view.CircledImageView;
import android.support.wearable.view.DotsPageIndicator;
import android.support.wearable.view.GridViewPager;
import android.support.wearable.view.WatchViewStub;
import android.support.wearable.view.WearableListView;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.TextView;
import android.widget.Toast;

import com.google.android.gms.wearable.DataMap;
import com.mariux.teleport.lib.TeleportClient;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.zip.Inflater;
import android.support.wearable.view.WearableListView;

public class MainActivity extends Activity implements SensorEventListener {


    private static final String TAG = "Sensor";
    private static String tripStartTime = "";
    private static boolean isTripStart;

    //UI Elements
    private CircledImageView mCircledImageView;
    private TextView mTextView;
    private Button mButton;

    // API
    TeleportClient mTeleportClient;
    TeleportClient.OnGetMessageTask mMessageTask;

    boolean isFromNotification;
//    private TextView mHeader;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        ArrayList<Integer> mIcons = new ArrayList<Integer>();
        mIcons.add(R.drawable.grey_dot);
        mIcons.add(R.drawable.green_arrow);
        mIcons.add(R.drawable.red_arrow);
        mIcons.add(R.drawable.grey_dot);
        mIcons.add(R.drawable.grey_dot);
        mIcons.add(R.drawable.grey_dot);
        mIcons.add(R.drawable.grey_dot);
        mIcons.add(R.drawable.green_arrow);
        mIcons.add(R.drawable.red_arrow);
        mIcons.add(R.drawable.green_arrow);
        mIcons.add(R.drawable.red_arrow);
        mIcons.add(R.drawable.grey_dot);
        mIcons.add(R.drawable.green_arrow);
        mIcons.add(R.drawable.red_arrow);
        mIcons.add(R.drawable.green_arrow);
        mIcons.add(R.drawable.green_arrow);
        mIcons.add(R.drawable.green_arrow);


        mTeleportClient = new TeleportClient(this);

        mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());

        mMessageTask = new ShowToastFromOnGetMessageTask();

        mTeleportClient.setOnGetMessageTask(mMessageTask);

        isFromNotification = getIntent().getBooleanExtra("FromNotification", false);

        retrieveTripInfo();

        stopService(new Intent(this, SensorService.class));
        startService(new Intent(this, SensorService.class));

        LayoutInflater inflater = LayoutInflater.from(this);

        //View
        final WatchViewStub stub = (WatchViewStub) inflater.inflate(R.layout.heart_layout, null, false).findViewById(R.id.watch_view_stub);
        stub.setOnLayoutInflatedListener(new WatchViewStub.OnLayoutInflatedListener() {
            @Override
            public void onLayoutInflated(WatchViewStub stub) {
                mCircledImageView = (CircledImageView) stub.findViewById(R.id.circle);
                mTextView = (TextView) stub.findViewById(R.id.value);
                mButton = (Button) stub.findViewById(R.id.startTripBtn);
            }
        });

        FrameLayout leaderboardFrame =
                (FrameLayout) inflater.inflate(R.layout.leaderboard, null, false);
//        mHeader = (TextView) leaderboardFrame.findViewById(R.id.header);
        WearableListView wearableListView=(WearableListView) leaderboardFrame.findViewById(R.id.wearable_List);
        wearableListView.setAdapter(new WearableAdapter(this, mIcons));
        wearableListView.setClickListener(mClickListener);
        wearableListView.addOnScrollListener(mOnScrollListener);
        GridViewPager pager = (GridViewPager) findViewById(R.id.pager);
        GridViewPagerAdapter adapter = new GridViewPagerAdapter(this, stub, leaderboardFrame);

        pager.setAdapter(adapter);
        DotsPageIndicator indicator = (DotsPageIndicator) findViewById(R.id.page_indicator);
        indicator.setPager(pager);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (mTeleportClient == null) {
            mTeleportClient = new TeleportClient(this);
            mTeleportClient.setOnSyncDataItemTask(new ShowToastHelloWorldTask());
        }
        mTeleportClient.connect();
    }

    @Override
    protected void onPause() {
        super.onPause();
    }

    @Override
    public void onSensorChanged(SensorEvent event) {
        //Update your data. This check is very raw. You should improve it when the sensor is unable to calculate the heart rate
        if (event.sensor.getType() == Sensor.TYPE_HEART_RATE) {
            if ((int)event.values[0]>0) {
                mCircledImageView.setCircleColor(getResources().getColor(R.color.green));
                mTextView.setText("" + (int) event.values[0]);
            }
        }
        Log.d(TAG, event.toString());
    }

    @Override
    public void onAccuracyChanged(Sensor sensor, int accuracy) {

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

    public void sendMessage(View v) {
        mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());

        if (!isTripStart) {
            startTrip();
        } else {
            stopTrip();
        }
    }

    public class ShowToastHelloWorldTask extends TeleportClient.OnSyncDataItemTask {

        @Override
        protected void onPostExecute(DataMap result) {
            String hello = result.getString("hello");

            Toast.makeText(getApplicationContext(),hello, Toast.LENGTH_SHORT).show();
        }
    }

    //Task that shows the path of a received message
    public class ShowToastFromOnGetMessageTask extends TeleportClient.OnGetMessageTask {

        @Override
        protected void onPostExecute(String  path) {

            Toast.makeText(getApplicationContext(),"Message - "+path,Toast.LENGTH_SHORT).show();

            //let's reset the task (otherwise it will be executed only once)
            mTeleportClient.setOnGetMessageTask(new ShowToastFromOnGetMessageTask());
        }
    }

    public void retrieveTripInfo(){
        SharedPreferences settings;
        settings = getSharedPreferences("TRIP_INFO", Context.MODE_PRIVATE);

        tripStartTime = settings.getString("START_TIME", "");
        isTripStart = settings.getBoolean("IS_TRIP_START", false);
        changeButtonText();
    }

    public void changeButtonText(){
        if (mButton != null) {
            mButton.setText(isTripStart ? "End Trip" : "Start Trip");
        }
    }

    public void startTrip(){
        SharedPreferences settings;
        settings = getSharedPreferences("TRIP_INFO", Context.MODE_PRIVATE);

        Calendar c = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("dd:MMMM:yyyy HH:mm:ss ");
        String strDate = sdf.format(c.getTime());

        SharedPreferences.Editor editor = settings.edit();
        editor.putString("START_TIME", strDate);
        editor.putBoolean("IS_TRIP_START", true);
        editor.commit();

        tripStartTime = strDate;
        isTripStart = true;
        changeButtonText();

        mTeleportClient.sendMessage("From Watch - Trip Start At: " + strDate, null);
    }

    public void stopTrip(){
        SharedPreferences settings;
        settings = getSharedPreferences("TRIP_INFO", Context.MODE_PRIVATE);
        SharedPreferences.Editor editor = settings.edit();
        editor.putBoolean("IS_TRIP_START", false);
        editor.commit();

        Calendar c = Calendar.getInstance();
        SimpleDateFormat sdf = new SimpleDateFormat("dd:MMMM:yyyy HH:mm:ss ");
        String strDate = sdf.format(c.getTime());

        isTripStart = false;
        changeButtonText();

        mTeleportClient.sendMessage("From Watch - Trip Stop At: " + strDate, null);
    }

    // Handle our Wearable List's click events
    private WearableListView.ClickListener mClickListener =
            new WearableListView.ClickListener() {
                @Override
                public void onClick(WearableListView.ViewHolder viewHolder) {
//                    Toast.makeText(MainActivity.this,
//                            String.format("You selected item #%s",
//                                    viewHolder.getLayoutPosition()+1),
//                            Toast.LENGTH_SHORT).show();
                }

                @Override
                public void onTopEmptyRegionClick() {
                    Toast.makeText(MainActivity.this,
                            "Top empty area tapped", Toast.LENGTH_SHORT).show();
                }
            };

    // The following code ensures that the title scrolls as the user scrolls up
    // or down the list
    private WearableListView.OnScrollListener mOnScrollListener =
            new WearableListView.OnScrollListener() {
                @Override
                public void onAbsoluteScrollChange(int i) {
                    // Only scroll the title up from its original base position
                    // and not down.
                    if (i > 0) {
//                        mHeader.setY(-i);
                    }
                }

                @Override
                public void onScroll(int i) {
                    // Placeholder
                }

                @Override
                public void onScrollStateChanged(int i) {
                    // Placeholder
                }

                @Override
                public void onCentralPositionChanged(int i) {
                    // Placeholder
                }
            };
}
