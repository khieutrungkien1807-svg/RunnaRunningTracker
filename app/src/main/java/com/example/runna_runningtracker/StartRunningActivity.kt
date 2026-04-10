package com.example.runna_runningtracker

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity

class StartRunningActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_start_running)

        val btnStart = findViewById<Button>(R.id.btnStart)
        val navHome = findViewById<View>(R.id.navHome)
        val navStart = findViewById<View>(R.id.navStart)
        val navHistory = findViewById<View>(R.id.navHistory)
        val navProfile = findViewById<View>(R.id.navProfile)

        btnStart.setOnClickListener {
            Toast.makeText(this, getString(R.string.start_run_demo_message), Toast.LENGTH_SHORT).show()
        }

        navHome.setOnClickListener { startActivity(Intent(this, HomeActivity::class.java)) }
        navStart.setOnClickListener { }
        navHistory.setOnClickListener { startActivity(Intent(this, HistoryActivity::class.java)) }
        navProfile.setOnClickListener { startActivity(Intent(this, ProfileActivity::class.java)) }
    }
}
