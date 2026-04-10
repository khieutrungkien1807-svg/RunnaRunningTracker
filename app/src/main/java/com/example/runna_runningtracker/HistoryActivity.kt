package com.example.runna_runningtracker

import android.content.Intent
import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity

class HistoryActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_history)

        val navHome = findViewById<View>(R.id.navHome)
        val navStart = findViewById<View>(R.id.navStart)
        val navHistory = findViewById<View>(R.id.navHistory)
        val navProfile = findViewById<View>(R.id.navProfile)

        navHome.setOnClickListener { startActivity(Intent(this, HomeActivity::class.java)) }
        navStart.setOnClickListener { startActivity(Intent(this, StartRunningActivity::class.java)) }
        navHistory.setOnClickListener { }
        navProfile.setOnClickListener { startActivity(Intent(this, ProfileActivity::class.java)) }
    }
}
