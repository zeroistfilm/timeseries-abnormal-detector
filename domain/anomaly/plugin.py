from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class Rule:
    """이상 탐지 규칙"""
    measurement: str
    max: float
    min: float
    rule_owner: str
    type: str
    rule_id: str
    description: str
    if_matched: str
    level: str


@dataclass
class RuleMatchContext:
    """이상 탐지를 위한 입력되는 데이터 정보"""
    topic: str
    current_value: float
    timestamp: datetime
    history: List[Any]
    metadata: Dict = None


@dataclass
class RuleMatchResult:
    """이상 탐지 결과"""
    isRuleMatch: bool
    details: Dict[str, Any]
    timestamp: datetime
    topic: str
    rule_id: str


class RuleMatchDetector(ABC):
    """이상 탐지 플러그인 기본 클래스"""

    @abstractmethod
    def detect(self, context: RuleMatchContext) -> List[RuleMatchResult]:
        pass


class ThresholdDetector(RuleMatchDetector):
    """임계값 기반 이상 탐지 플러그인"""

    def __init__(self, rule: Rule):
        """
        Initializes with a single rule.
        Each detector manages one rule for modularity.
        """
        self.rule = rule
        self.type = rule.type
        self.rule_owner = rule.rule_owner

    def check_rule(self, context: RuleMatchContext) -> Optional[RuleMatchResult]:
        """단일 규칙 검사"""
        current_value = context.current_value
        timestamp = context.timestamp

        min_val = self.rule.min
        max_val = self.rule.max

        isRuleMatch = False
        if min_val is not None and max_val is not None:
            isRuleMatch = min_val <= current_value < max_val

        if isRuleMatch:
            return RuleMatchResult(
                isRuleMatch=True,
                details={
                    'description': self.rule.description,
                    'level': self.rule.level,
                    'type': self.type,
                    'rule_owner': self.rule_owner,
                    'value': current_value,
                    'max': max_val,
                    'min': min_val,

                },
                rule_id=self.rule.rule_id,
                topic=context.topic,
                timestamp=timestamp

            )
        return None

    def detect(self, context: RuleMatchContext) -> List[RuleMatchResult]:
        """현재 값을 기준으로 단일 규칙 평가"""

        result = self.check_rule(context)
        return [result] if result else []


class RuleMatchDetectorManager:
    """이상 탐지 플러그인 관리자"""

    def __init__(self):
        self.plugins: List[RuleMatchDetector] = []

    def add_detectors(self, rules: List[Rule]):
        """여러 규칙을 기반으로 탐지기를 추가"""
        for rule in rules:
            if rule.type == 'threshold':
                detector = ThresholdDetector(rule)
                self.plugins.append(detector)

            # 향후 다른 탐지기 유형 추가 가능
            # elif detector_type == 'other_type':
            #     detector = OtherTypeDetector(rule)
            #     self.plugins.append(detector)

    def detect_all(self, context: RuleMatchContext) -> List[RuleMatchResult]:
        """모든 플러그인으로 이상 탐지 수행"""
        all_results = []
        for plugin in self.plugins:
            results = plugin.detect(context)
            all_results.extend(results)
        return all_results
