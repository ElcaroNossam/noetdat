from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("screener", "0001_initial"),
    ]

    operations = [
        # Price change (%)
        migrations.AddField(
            model_name="screenersnapshot",
            name="change_1d",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="change_1h",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="change_5m",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="change_8h",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="change_15m",
            field=models.FloatField(default=0.0),
        ),
        # OI change (%)
        migrations.AddField(
            model_name="screenersnapshot",
            name="oi_change_1d",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="oi_change_8h",
            field=models.FloatField(default=0.0),
        ),
        # Core open interest
        migrations.AddField(
            model_name="screenersnapshot",
            name="open_interest",
            field=models.FloatField(default=0.0),
        ),
        # New ticks granularity
        migrations.AddField(
            model_name="screenersnapshot",
            name="ticks_1h",
            field=models.IntegerField(default=0),
        ),
        # Vdelta extended horizons
        migrations.AddField(
            model_name="screenersnapshot",
            name="vdelta_1d",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="vdelta_1h",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="vdelta_8h",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="vdelta_15m",
            field=models.FloatField(default=0.0),
        ),
        # Volatility 5m/1h (15m existed before)
        migrations.AddField(
            model_name="screenersnapshot",
            name="volatility_1h",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="volatility_5m",
            field=models.FloatField(default=0.0),
        ),
        # Extended volume windows
        migrations.AddField(
            model_name="screenersnapshot",
            name="volume_1d",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="volume_8h",
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name="screenersnapshot",
            name="volume_15m",
            field=models.FloatField(default=0.0),
        ),
    ]


