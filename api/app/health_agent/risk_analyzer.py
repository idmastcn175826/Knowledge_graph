# app/utils/risk_analyzer.py
class RiskAnalyzer:
    # 医学标准阈值
    MEDICAL_THRESHOLDS = {
        "heart_rate": {"min": 60, "max": 100, "critical_min": 40, "critical_max": 130},
        "blood_oxygen": {"min": 95, "critical_min": 90},
        "systolic_bp": {"min": 90, "max": 140, "critical_min": 80, "critical_max": 180},
        "diastolic_bp": {"min": 60, "max": 90, "critical_min": 50, "critical_max": 110},
        "blood_glucose": {"min": 3.9, "max": 6.1, "critical_min": 3.0, "critical_max": 16.7}
    }

    @classmethod
    def analyze(cls, health_data):
        """分析健康数据风险等级"""
        # 获取用户基线数据（实际应用中应从数据库获取）
        user_baseline = cls.get_user_baseline(health_data.user_id)

        # 检查关键指标是否超过紧急阈值
        if cls.check_critical_conditions(health_data):
            return "critical"

        # 检查是否超过医学警告阈值
        if cls.check_warning_conditions(health_data):
            return "warning"

        # 检查是否偏离个人基线
        if cls.check_personal_deviations(health_data, user_baseline):
            return "mild"

        return "normal"

    @classmethod
    def check_critical_conditions(cls, health_data):
        """检查是否达到紧急医疗条件"""
        if (health_data.heart_rate and
                (health_data.heart_rate <= cls.MEDICAL_THRESHOLDS["heart_rate"]["critical_min"] or
                 health_data.heart_rate >= cls.MEDICAL_THRESHOLDS["heart_rate"]["critical_max"])):
            return True

        if (health_data.blood_oxygen and
                health_data.blood_oxygen <= cls.MEDICAL_THRESHOLDS["blood_oxygen"]["critical_min"]):
            return True

        # 检查其他关键指标...
        return False

