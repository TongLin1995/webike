package com.example.carl.urawear;

import android.os.Environment;
import android.util.Log;

import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.List;
import java.util.Locale;

/**
 * Created by carl on 7/30/15.
 */
public class URAWearLog {

    private static List<String> datalogs = new ArrayList<String>();
    private static String wearTag = "URAWear";

    public static String DataLogDirectory = Environment.getExternalStorageDirectory().getAbsolutePath() + File.separator + "sensordc" + File.separator + "data";

    public static void e(String tag, String message, Class cls)
    {
        Log.e(tag, message);
    }

    public static void i(String tag, String message, Class cls)
    {
        Log.i(tag, message);
    }

    public static void i(String message, Class cls)
    {
        Log.i(wearTag, message);
    }

    public static void data(String ts, String data, Class cls)
    {
        synchronized (datalogs)
        {
            Log.i(wearTag, data);
            datalogs.add(ts + "," + cls.getName() + "," + data);
        }
    }

    public static void DumpDataLogsToDisk()
    {
        synchronized (datalogs)
        {
            for (String line : datalogs)
            {
                WriteToFile(line + "\n");
            }
            datalogs.clear();
        }
    }

    public static String getCurrentTimeStamp()
    {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss.SSS", Locale.CANADA);
        String ts = sdf.format(Calendar.getInstance().getTime());
        return ts;
    }

    public static String getCurrentFileName()
    {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd-HH", Locale.CANADA);
        String date_hour = sdf.format(Calendar.getInstance().getTime());
        return "watchDataV1." + date_hour + ".log";
    }

    private static void WriteToFile(String message)
    {
        try
        {
            String filename = getCurrentFileName();
            File path = new File(DataLogDirectory);
            path.mkdirs();

            File myFile = new File(path, filename);
            if (!myFile.exists())
            {
                myFile.createNewFile();
            }

            try
            {
                byte[] data = message.getBytes();

                FileOutputStream fos = new FileOutputStream(myFile, true);
                BufferedOutputStream output = new BufferedOutputStream(fos);
                output.write(data);
                output.flush();
                output.close();
            } catch (FileNotFoundException e)
            {
                Log.e(wearTag, filename + " FileNotFoundException " + e.getLocalizedMessage());
                e.printStackTrace();
            }
        } catch (Exception e)
        {
            Log.e(wearTag, "" + e.getLocalizedMessage());
            e.printStackTrace();
        }

    }

}
