package com.example.carl.urawear;

import android.content.Context;
import android.support.wearable.view.CircledImageView;
import android.support.wearable.view.WearableListView;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import java.util.ArrayList;
import java.util.Random;

public class WearableAdapter extends WearableListView.Adapter {
    private ArrayList<Integer> mItems;
    private final LayoutInflater mInflater;

    public WearableAdapter(Context context, ArrayList<Integer> items) {
        mInflater = LayoutInflater.from(context);
        mItems = items;
    }

    @Override
    public WearableListView.ViewHolder onCreateViewHolder(
            ViewGroup viewGroup, int i) {
        return new ItemViewHolder(mInflater.inflate(R.layout.list_item, null));
    }

    @Override
    public void onBindViewHolder(WearableListView.ViewHolder viewHolder,
                                 int position) {
        ItemViewHolder itemViewHolder = (ItemViewHolder) viewHolder;
        CircledImageView circledView = itemViewHolder.mCircledImageView;
        circledView.setImageResource(mItems.get(position));
        TextView rankView = itemViewHolder.mItemTextViewRank;
        rankView.setText(String.format("%d.",position+1));
        TextView textView = itemViewHolder.mItemTextViewName;
        textView.setText(String.format("Participant %d", position + 1));
        TextView pointsView = itemViewHolder.mItemTextViewPoints;
        Random random = new Random();
        pointsView.setText(String.format("(%d)",10000-( 1000 + 100*position + random.nextInt(99))));
    }

    @Override
    public int getItemCount() {
        return mItems.size();
    }

    private static class ItemViewHolder extends WearableListView.ViewHolder {
        private CircledImageView mCircledImageView;
        private TextView mItemTextViewName;
        private TextView mItemTextViewRank;
        private TextView mItemTextViewPoints;

        public ItemViewHolder(View itemView) {
            super(itemView);
            mCircledImageView = (CircledImageView)
                    itemView.findViewById(R.id.circle);
            mItemTextViewName = (TextView) itemView.findViewById(R.id.name);
            mItemTextViewRank = (TextView) itemView.findViewById(R.id.rank);
            mItemTextViewPoints = (TextView) itemView.findViewById(R.id.points);
        }
    }
}