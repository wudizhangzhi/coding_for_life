import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (Column, Integer, String, CHAR, TEXT, DATE, DATETIME, ForeignKey, create_engine)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.ext.indexable import index_property
from sqlalchemy.orm import (sessionmaker, relationship)


# 创建对象的基类:
Base = declarative_base()
# 初始化数据库连接:
try:
    engine = create_engine('mysql+pymysql://root:@localhost:3306/shenqi?charset=utf8mb4', echo=False)
except ModuleNotFoundError:
    engine = create_engine('mysql+mysqldb://root:@localhost:3306/shenqi?charset=utf8mb4', echo=False)


class Device(Base):
    __tablename__ = 'device'

    id = Column(Integer, primary_key=True, nullable=False)
    setCpuName = Column(String(255), nullable=False)
    getString = Column(String(255), nullable=False)
    getNetworkType = Column(String(255), nullable=False)
    getPhoneType = Column(String(255), nullable=False)
    hardware = Column(String(255), nullable=False)
    getMetrics = Column(TEXT, nullable=False)
    getSimOperatorName = Column(String(255), nullable=True)
    getNetworkCountryIso = Column(String(255), nullable=True)
    getMacAddress = Column(String(255), nullable=True)
    getSimState = Column(String(255), nullable=False)
    connectType = Column(String(255), nullable=False)
    getSimSerialNumber = Column(String(255), nullable=False)
    getDeviceId = Column(String(255), nullable=False)  # 设备id
    board = Column(String(255), nullable=False)
    sdk = Column(String(255), nullable=False)
    getSsid = Column(String(255), nullable=False)
    getSimOperator = Column(String(255), nullable=True)
    product = Column(String(255), nullable=False)  # 产品
    getNetworkOperatorName = Column(String(255), nullable=False)
    getRadioVersion1 = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=False)  # 品牌
    getSubscriberId = Column(String(255), nullable=False)
    getString2 = Column(String(255), nullable=False)
    getLine1number = Column(String(255), nullable=False)
    fingerprint = Column(String(255), nullable=False)
    device = Column(String(255), nullable=False)
    bootloader = Column(String(255), nullable=False)
    arch = Column(String(255), nullable=False)
    manufacturer = Column(String(255), nullable=False)
    getRadioVersion = Column(String(255), nullable=False)
    getBssid = Column(String(255), nullable=False)
    getSimCountryIso = Column(String(255), nullable=True)
    getNetworkOperator = Column(String(255), nullable=True)
    getJiZhan = Column(String(255), nullable=False)
    release = Column(String(255), nullable=False)  # android版本号
    model = Column(String(255), nullable=False, index=True)  # 品牌型号

    def __str__(self):
        return '{}'.format(self.model)

def init_db():
    drop_db()
    Base.metadata.create_all(engine)

def drop_db():
    Base.metadata.drop_all(engine)

def test():
    init_db()
    # 创建DBSession类型:
    DBSession = sessionmaker(bind=engine)
    # 创建session对象:
    session = DBSession()
    query = session.query(Device)
    print(query)
    r = query.all()
    print(r)
    session.rollback()

    # insert jrs
    # jrs = JRS(uid=123456, name='jack')
    # session.add(jrs)
    # session.commit()

if __name__ == '__main__':
    test()
