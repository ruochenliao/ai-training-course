from datetime import timedelta, timezone

from fastapi import APIRouter, HTTPException

from ....controllers.user import user_controller
from ....core.ctx import CTX_USER_ID
from ....core.dependency import DependAuth
from ....models.admin import Api, Menu, Role, User
from ....schemas.base import Success
from ....schemas.login import *
from ....schemas.users import UpdatePassword
from ....settings import settings
from ....utils.jwt import create_access_token
from ....utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    try:
        user: User = await user_controller.authenticate(credentials)
        await user_controller.update_last_login(user.id)
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.now(timezone.utc) + access_token_expires

        data = JWTOut(
            access_token=create_access_token(
                data=JWTPayload(
                    user_id=user.id,
                    username=user.username,
                    is_superuser=user.is_superuser,
                    exp=expire,
                )
            ),
            username=user.username,
        )
        return Success(data=data.model_dump())
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"认证失败: {str(e)}")


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    try:
        user_id = CTX_USER_ID.get()
        user_obj = await user_controller.get(id=user_id)
        data = await user_obj.to_dict(exclude_fields=["password"])
        data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
        return Success(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    try:
        user_id = CTX_USER_ID.get()
        user_obj = await User.filter(id=user_id).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")

        menus: list[Menu] = []
        if user_obj.is_superuser:
            menus = await Menu.all()
        else:
            role_objs: list[Role] = await user_obj.roles
            for role_obj in role_objs:
                menu = await role_obj.menus
                menus.extend(menu)
            menus = list(set(menus))
        parent_menus: list[Menu] = []
        for menu in menus:
            if menu.parent_id == 0:
                parent_menus.append(menu)
        res = []
        for parent_menu in parent_menus:
            parent_menu_dict = await parent_menu.to_dict()
            parent_menu_dict["children"] = []
            for menu in menus:
                if menu.parent_id == parent_menu.id:
                    parent_menu_dict["children"].append(await menu.to_dict())
            res.append(parent_menu_dict)
        return Success(data=res)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户菜单失败: {str(e)}")


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    try:
        user_id = CTX_USER_ID.get()
        user_obj = await User.filter(id=user_id).first()
        if not user_obj:
            raise HTTPException(status_code=404, detail="用户不存在")

        if user_obj.is_superuser:
            api_objs: list[Api] = await Api.all()
            apis = [api.method.lower() + api.path for api in api_objs]
            return Success(data=apis)
        role_objs: list[Role] = await user_obj.roles
        apis = []
        for role_obj in role_objs:
            api_objs: list[Api] = await role_obj.apis
            apis.extend([api.method.lower() + api.path for api in api_objs])
        apis = list(set(apis))
        return Success(data=apis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户API失败: {str(e)}")


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    try:
        user_id = CTX_USER_ID.get()
        user = await user_controller.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        verified = verify_password(req_in.old_password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="旧密码验证错误")

        user.password = get_password_hash(req_in.new_password)
        await user.save()
        return Success(msg="修改成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"修改密码失败: {str(e)}")
