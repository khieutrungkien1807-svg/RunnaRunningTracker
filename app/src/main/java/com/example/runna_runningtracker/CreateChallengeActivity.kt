package com.example.runna_runningtracker

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity

class CreateChallengeActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_create_challenge)

        val btnBack = findViewById<View>(R.id.btnBack)
        btnBack.setOnClickListener { finish() }

        val btnCreate = findViewById<View>(R.id.btnCreate)
        btnCreate.setOnClickListener { finish() }
    }
}
