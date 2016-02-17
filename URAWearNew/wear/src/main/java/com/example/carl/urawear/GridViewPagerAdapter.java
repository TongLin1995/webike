package com.example.carl.urawear;

import android.content.Context;
import android.support.wearable.view.GridPagerAdapter;
import android.support.wearable.view.WatchViewStub;
import android.support.wearable.view.WearableListView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.TextView;

class GridViewPagerAdapter extends GridPagerAdapter {
    private final LayoutInflater mInflater;
    private final Context context;
    private final WatchViewStub stub;
    private FrameLayout leaderboard;

    public GridViewPagerAdapter(Context context, WatchViewStub stub, FrameLayout leaderboard) {
        this.context = context;
        this.stub = stub;
        this.leaderboard = leaderboard;
        mInflater = LayoutInflater.from(context);
    }

    @Override
    public int getColumnCount(int arg0) {
        return 2;
    }

    @Override
    public int getRowCount() {
        return 1;
    }

    @Override
    public Object instantiateItem(ViewGroup container, int row, int col) {

        if(col==0) {
            container.addView(stub);
            return stub;
        }
        else {
            container.addView(leaderboard);
            return leaderboard;
        }
    }

    @Override
    public void destroyItem(ViewGroup container, int row, int col, Object view) {
        container.removeView((View)view);
    }

    @Override
    public boolean isViewFromObject(View view, Object object) {
        return view==object;
    }
}