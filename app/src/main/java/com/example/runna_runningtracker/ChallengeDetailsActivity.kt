package com.example.runna_runningtracker

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity

class ChallengeDetailsActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_challenge_details)

        val btnBack = findViewById<View>(R.id.btnBack)
        btnBack.setOnClickListener { finish() }
    }
}
