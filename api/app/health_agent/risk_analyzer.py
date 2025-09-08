# app/utils/risk_analyzer.py
from app.db.session import get_db
from app.models.health import HealthData
from sqlalchemy.orm import Session
import statistics


class RiskAnalyzer:
    # 医学标准阈值
    MEDICAL_THRESHOLDS = {
        "heart_rate": {"min": 60, "max": 100, "critical_min": 40, "critical_max": 130},
        "blood_oxygen": {"min": 95, "critical_min": 90},
        "systolic_bp": {"min": 90, "max": 140, "critical_min": 80, "critical_max": 180},
        "diastolic_bp": {"min": 60, "max": 90, "critical_min": 50, "critical_max": 110},
        "blood_glucose": {"min": 3.9, "max": 6.1, "critical_min": 3.0, "critical_max": 16.7}
    }

    # 个人基线偏差阈值（百分比）
    BASELINE_DEVIATION_THRESHOLDS = {
        "heart_rate": 0.2,  # 20%
        "blood_oxygen": 0.05,  # 5%
        "systolic_bp": 0.15,  # 15%
        "diastolic_bp": 0.15,  # 15%
        "blood_glucose": 0.2  # 20%
    }

    @classmethod
    def analyze(cls, health_data):
        """分析健康数据风险等级"""
        # 获取用户基线数据
        user_baseline = cls.get_user_baseline(health_data.user_id)

        # 检查关键指标是否超过紧急阈值
        if cls.check_critical_conditions(health_data):
            return "critical"

        # 检查是否超过医学警告阈值
        if cls.check_warning_conditions(health_data):
            return "warning"

        # 检查是否偏离个人基线
        if user_baseline and cls.check_personal_deviations(health_data, user_baseline):
            return "mild"

        return "normal"

    @classmethod
    def get_user_baseline(cls, user_id: int):
        """获取用户的健康基线数据（历史平均值）"""
        if not user_id:
            return None

        # 获取数据库会话
        db: Session = next(get_db())

        try:
            # 查询用户最近30条健康数据作为基线参考
            recent_data = db.query(HealthData).filter(
                HealthData.user_id == user_id
            ).order_by(HealthData.timestamp.desc()).limit(30).all()

            if not recent_data:
                return None

            # 计算各健康指标的平均值
            baseline = {}

            # 心率平均值
            heart_rates = [d.heart_rate for d in recent_data if d.heart_rate is not None]
            if heart_rates:
                baseline['heart_rate'] = statistics.mean(heart_rates)

            # 血氧平均值
            blood_oxygens = [d.blood_oxygen for d in recent_data if d.blood_oxygen is not None]
            if blood_oxygens:
                baseline['blood_oxygen'] = statistics.mean(blood_oxygens)

            # 收缩压平均值
            systolic_bps = [d.systolic_bp for d in recent_data if d.systolic_bp is not None]
            if systolic_bps:
                baseline['systolic_bp'] = statistics.mean(systolic_bps)

            # 舒张压平均值
            diastolic_bps = [d.diastolic_bp for d in recent_data if d.diastolic_bp is not None]
            if diastolic_bps:
                baseline['diastolic_bp'] = statistics.mean(diastolic_bps)

            # 血糖平均值
            blood_glucoses = [d.blood_glucose for d in recent_data if d.blood_glucose is not None]
            if blood_glucoses:
                baseline['blood_glucose'] = statistics.mean(blood_glucoses)

            return baseline

        finally:
            # 关闭数据库会话
            db.close()

    @classmethod
    def check_critical_conditions(cls, health_data):
        """检查是否达到紧急医疗条件"""
        # 心率紧急阈值检查
        if (health_data.heart_rate is not None and
                (health_data.heart_rate <= cls.MEDICAL_THRESHOLDS["heart_rate"]["critical_min"] or
                 health_data.heart_rate >= cls.MEDICAL_THRESHOLDS["heart_rate"]["critical_max"])):
            return True

        # 血氧紧急阈值检查
        if (health_data.blood_oxygen is not None and
                health_data.blood_oxygen <= cls.MEDICAL_THRESHOLDS["blood_oxygen"]["critical_min"]):
            return True

        # 收缩压紧急阈值检查
        if (health_data.systolic_bp is not None and
                (health_data.systolic_bp <= cls.MEDICAL_THRESHOLDS["systolic_bp"]["critical_min"] or
                 health_data.systolic_bp >= cls.MEDICAL_THRESHOLDS["systolic_bp"]["critical_max"])):
            return True

        # 舒张压紧急阈值检查
        if (health_data.diastolic_bp is not None and
                (health_data.diastolic_bp <= cls.MEDICAL_THRESHOLDS["diastolic_bp"]["critical_min"] or
                 health_data.diastolic_bp >= cls.MEDICAL_THRESHOLDS["diastolic_bp"]["critical_max"])):
            return True

        # 血糖紧急阈值检查
        if (health_data.blood_glucose is not None and
                (health_data.blood_glucose <= cls.MEDICAL_THRESHOLDS["blood_glucose"]["critical_min"] or
                 health_data.blood_glucose >= cls.MEDICAL_THRESHOLDS["blood_glucose"]["critical_max"])):
            return True

        return False

    @classmethod
    def check_warning_conditions(cls, health_data):
        """检查是否超过医学警告阈值（但未达到紧急程度）"""
        # 心率警告阈值检查
        if (health_data.heart_rate is not None and
                (health_data.heart_rate < cls.MEDICAL_THRESHOLDS["heart_rate"]["min"] or
                 health_data.heart_rate > cls.MEDICAL_THRESHOLDS["heart_rate"]["max"])):
            return True

        # 血氧警告阈值检查
        if (health_data.blood_oxygen is not None and
                health_data.blood_oxygen < cls.MEDICAL_THRESHOLDS["blood_oxygen"]["min"]):
            return True

        # 收缩压警告阈值检查
        if (health_data.systolic_bp is not None and
                (health_data.systolic_bp < cls.MEDICAL_THRESHOLDS["systolic_bp"]["min"] or
                 health_data.systolic_bp > cls.MEDICAL_THRESHOLDS["systolic_bp"]["max"])):
            return True

        # 舒张压警告阈值检查
        if (health_data.diastolic_bp is not None and
                (health_data.diastolic_bp < cls.MEDICAL_THRESHOLDS["diastolic_bp"]["min"] or
                 health_data.diastolic_bp > cls.MEDICAL_THRESHOLDS["diastolic_bp"]["max"])):
            return True

        # 血糖警告阈值检查
        if (health_data.blood_glucose is not None and
                (health_data.blood_glucose < cls.MEDICAL_THRESHOLDS["blood_glucose"]["min"] or
                 health_data.blood_glucose > cls.MEDICAL_THRESHOLDS["blood_glucose"]["max"])):
            return True

        return False

    @classmethod
    def check_personal_deviations(cls, health_data, user_baseline):
        """检查是否偏离个人基线"""
        # 心率偏离检查
        if (health_data.heart_rate is not None and
                'heart_rate' in user_baseline and
                user_baseline['heart_rate'] > 0):

            deviation = abs(health_data.heart_rate - user_baseline['heart_rate']) / user_baseline['heart_rate']
            if deviation > cls.BASELINE_DEVIATION_THRESHOLDS["heart_rate"]:
                return True

        # 血氧偏离检查
        if (health_data.blood_oxygen is not None and
                'blood_oxygen' in user_baseline and
                user_baseline['blood_oxygen'] > 0):

            deviation = abs(health_data.blood_oxygen - user_baseline['blood_oxygen']) / user_baseline['blood_oxygen']
            if deviation > cls.BASELINE_DEVIATION_THRESHOLDS["blood_oxygen"]:
                return True

        # 收缩压偏离检查
        if (health_data.systolic_bp is not None and
                'systolic_bp' in user_baseline and
                user_baseline['systolic_bp'] > 0):

            deviation = abs(health_data.systolic_bp - user_baseline['systolic_bp']) / user_baseline['systolic_bp']
            if deviation > cls.BASELINE_DEVIATION_THRESHOLDS["systolic_bp"]:
                return True

        # 舒张压偏离检查
        if (health_data.diastolic_bp is not None and
                'diastolic_bp' in user_baseline and
                user_baseline['diastolic_bp'] > 0):

            deviation = abs(health_data.diastolic_bp - user_baseline['diastolic_bp']) / user_baseline['diastolic_bp']
            if deviation > cls.BASELINE_DEVIATION_THRESHOLDS["diastolic_bp"]:
                return True

        # 血糖偏离检查
        if (health_data.blood_glucose is not None and
                'blood_glucose' in user_baseline and
                user_baseline['blood_glucose'] > 0):

            deviation = abs(health_data.blood_glucose - user_baseline['blood_glucose']) / user_baseline['blood_glucose']
            if deviation > cls.BASELINE_DEVIATION_THRESHOLDS["blood_glucose"]:
                return True

        return False
